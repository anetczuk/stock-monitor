# MIT License
#
# Copyright (c) 2020 Arkadiusz Netczuk <dev.arnet@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from enum import Enum, unique
import logging
import datetime
from copy import deepcopy

from typing import List, Tuple

import numpy
from pandas.core.frame import DataFrame

## from stockdataaccess.pprint import pprint


_LOGGER = logging.getLogger(__name__)


## amount, unit_price, commission, transaction time
## amount > 0 -- buy transaction, otherwise sell transaction
#Transaction = Tuple[int, float, float, datetime]
class Transaction:

    def __init__(self, amount, unitPrice, commission, transTime: datetime.datetime):
        self.amount     = amount                ## amount > 0 -- buy transaction, otherwise sell transaction
        self.unitPrice  = unitPrice
        self.commission = commission
        self.transTime  = transTime

#     def __getitem__(self, key):
#         if key == 0:
#             return self.amount
#         if key == 1:
#             return self.unitPrice
#         raise IndexError( f"bad index: {key}" )

    ## unpack operator
    def __iter__(self):
        return iter( (self.amount, self.unitPrice, self.commission, self.transTime) )

    def isEmpty(self):
        return self.transTime is None

    def getValue( self, includeCommission=False ):
        transValue = self.amount * self.unitPrice
        if includeCommission:
            transValue += self.getCommission()
        return transValue

    ## returns always positive value
    def getCommission(self):
        if self.commission < 0.01:
            cost = abs( self.amount ) * self.unitPrice
            return broker_commission( cost, self.transTime )
        return self.commission

    def add(self, amount, commission):
        self.amount     += amount
        self.commission += commission

    def addAvg( self, item: "Transaction" ):
        currVal = self.getValue( False )
        addVal  = item.getValue( False )
        sumVal  = currVal + addVal

        self.amount     += item.amount
        self.unitPrice   = sumVal / self.amount
        self.commission += item.commission
        self.transTime   = item.transTime

    def reduceAmount(self, amount):
        self.commission *= 1.0 - float( amount ) / self.amount
        self.amount -= amount

    def __repr__(self):
        return f"({self.amount}, {self.unitPrice}, {self.commission}, {self.transTime})"

    @staticmethod
    def empty():
        return Transaction( 0, 0.0, 0.0, None )

    @staticmethod
    def sortDate( tuple1, tuple2 ):
        date1 = tuple1.transTime
        if date1 is None:
            return 1
        date2 = tuple2.transTime
        if date2 is None:
            return -1
        return date1 < date2

    @staticmethod
    def sortKey( tupleValue ):
        retDate = tupleValue.transTime
        if retDate is None:
            return datetime.datetime.min
        return retDate


## list of buy transactions
BuyTransactionsMatch  = List[ Transaction ]
## return list of pairs: buy transaction and it's matching sell transaction
SellTransactionsMatch = List[ Tuple[Transaction, Transaction] ]
## pair of lists: current (buy) transactions and matched sell transactions
TransactionsMatch     = Tuple[ BuyTransactionsMatch, SellTransactionsMatch ]


@unique
class TransactionMatchMode(Enum):
    OLDEST = ()             # FIFO
    BEST = ()
    RECENT_PROFIT = ()

    def __new__(cls):
        value = len(cls.__members__)  # note no + 1
        obj = object.__new__(cls)
        # pylint: disable=W0212
        obj._value_ = value
        return obj


# Transactions of single stock
class TransHistory():

    def __init__(self):
        ## most recent transaction on top (with index 0)
        self.transactions: List[ Transaction ] = []

    def __getitem__(self, index):
        return self.transactions[ index ]

    def __setitem__(self, index, value):
        self.transactions[ index ] = value

    def __len__(self):
        return len( self.transactions )

    def size(self):
        return len( self.transactions )

    def clear(self):
        self.transactions.clear()

    def items(self):
        return self.transactions

    def allTransactions(self):
        return self.transactions

    def currentAmount(self):
        stockAmount = 0
        for item in self.transactions:
            stockAmount += item.amount
        return stockAmount

    def amountBeforeDate(self, transDate):
        stockAmount = 0
        for item in self.transactions:
            itemDate = item.transTime.date()
            if itemDate < transDate:
                stockAmount += item.amount
        return stockAmount

    def append(self, amount, unitPrice, commission, transTime: datetime.datetime = None):
        self.transactions.insert( 0, Transaction(amount, unitPrice, commission, transTime) )

    def appendItem(self, item):
        self.transactions.insert( 0, Transaction( *item ) )

    def appendList(self, itemList):
        for item in itemList:
            self.appendItem( item )
        self.sort()

    def add(self, amount, unitPrice, commission, transTime=None, joinSimilar=True):
        if joinSimilar is False:
#                 _LOGGER.debug( "adding transaction: %s %s %s", amount, unitPrice, transTime )
            self.append( amount, unitPrice, commission, transTime )
            self.sort()
            return
        sameIndex = self._findSame( unitPrice, transTime, amount, commission )
        if sameIndex > -1:
            return
        similarIndex = self._findSimilar( unitPrice, transTime )
        if similarIndex < 0:
#                 _LOGGER.debug( "adding transaction: %s %s %s", amount, unitPrice, transTime )
            self.append( amount, unitPrice, commission, transTime )
            self.sort()
            return
        ## _LOGGER.debug( "joining transaction: %s %s %s %s", amount, unitPrice, commission, transTime )
        item = self.transactions[ similarIndex ]
        item.add( amount, commission )

    ## =============================================================

    ## find transaction pointed by 'findTime'
    def findIndex( self, findTime: datetime.datetime ) -> int:
        tSize = len( self.transactions )
        for i in range(0, tSize):
            item = self.transactions[ i ]
            transTime = item.transTime
            if findTime > transTime:             ## transactions are in reverse order
                return i
        return tSize

    ## find transaction with date before given date and return it's index
    def findIndexBefore( self, endDate: datetime.date ) -> int:
        tSize = len( self.transactions )
        for i in range(0, tSize):
            item = self.transactions[ i ]
            transTime = item.transTime
            transDate = transTime.date()
            if endDate > transDate:             ## transactions are in reverse order
                return i
        return tSize

    def splitTransactions( self, afterIndex: int, currentAfter=False ) -> Tuple['TransHistory', 'TransHistory']:
        if currentAfter is True:
            nextIndex = afterIndex + 1
            return self.splitTransactions( nextIndex, False )

        transList   = self.transactions[ afterIndex: ]
        beforeTrans = TransHistory()
        beforeTrans.appendList( transList )

        transList  = self.transactions[ : afterIndex ]
        afterTrans = TransHistory()
        afterTrans.appendList( transList )

        return ( beforeTrans, afterTrans )

    def transactionsBefore( self, endDate: datetime.date ) -> 'TransHistory':
        foundIndex = self.findIndexBefore( endDate )
        if foundIndex >= self.size():
            return TransHistory()
        transList = self.transactions[ foundIndex: ]
        retTrans  = TransHistory()
        retTrans.appendList( transList )
        return retTrans

    ## most recent transaction in front (first index)
    def transactionsAfter( self, startDate: datetime.date ) -> 'TransHistory':
        foundIndex = self.findIndexBefore( startDate )
        if foundIndex >= self.size():
            return TransHistory()
        transList = self.transactions[ : foundIndex ]
        retTrans  = TransHistory()
        retTrans.appendList( transList )
        return retTrans

    def groupByDay(self):
        transList = self.groupTransactionsByDay( self.transactions )
        retTrans = TransHistory()
        retTrans.appendList( transList )
        return retTrans

    @staticmethod
    def groupTransactionsByDay( transactions ):
        if len( transactions ) < 1:
            return transactions

        currDate  = None
        buyTrans  = Transaction.empty()
        sellTrans = Transaction.empty()

        transList = []
        #for item in self.transactions:
        for item in reversed( transactions ):
            transTime = item.transTime
            transDate = transTime.date()

            if transDate != currDate:
                ## next day -- store transactions
                if buyTrans.amount > 0:
                    transList.append( buyTrans )
                buyTrans = Transaction.empty()
                if sellTrans.amount < 0:
                    transList.append( sellTrans )
                sellTrans = Transaction.empty()

            currDate = transDate
            if item.amount > 0:
                buyTrans.addAvg( item )
            else:
                sellTrans.addAvg( item )

        ## add day transactions
        if buyTrans.amount > 0:
            transList.append( buyTrans )
        if sellTrans.amount < 0:
            transList.append( sellTrans )

        transList = reversed( transList )
        return transList

    ## buy transactions in wallet
    def currentTransactions( self, mode: TransactionMatchMode ) -> BuyTransactionsMatch:
        retPair = self.matchTransactions( mode )
        return retPair[0]

    ## average buy unit price of current amount of stock
    ## returns pair: (amount, unit_price)
    def currentTransactionsAvg(self, mode: TransactionMatchMode):
        ## Buy value raises then current unit price rises
        ## Sell value raises then current unit price decreases

        buyList = self.currentTransactions( mode )
        if not buyList:
            return (0, 0)

        currAmount = 0
        currValue  = 0.0
        for transItem in buyList:
            currAmount += transItem.amount
            currValue  += transItem.getValue( True )

        currUnitPrice = currValue / currAmount
        return ( currAmount, currUnitPrice )

    ## returns List[ (buy transaction, sell transaction) ]
    def sellTransactions(self, mode: TransactionMatchMode) -> SellTransactionsMatch:
        retPair = self.matchTransactions( mode )
        return retPair[1]

    ## return profit of sold transactions
    def transactionsGain(self, mode: TransactionMatchMode, considerCommission=True):
        totalGain = self.transactionsGainHistory( mode, considerCommission )
        if not totalGain:
            return 0.0
        lastItem = totalGain[-1]
        return lastItem[1]

    ## return list of pairs: [(data, value)]
    ## return values are calculated by difference: sell value - buy value in date (only already sold stock is considered)
    def transactionsGainHistory(self, mode: TransactionMatchMode, considerCommission=True, startDate=None ):
        ret: List[ List[object] ] = []
        totalGain: float = 0.0
        sellTransactions: SellTransactionsMatch = self.sellTransactions( mode )
        for buyTrans, sellTrans in sellTransactions:
            buyCost    = buyTrans.getValue( considerCommission )
            sellProfit = sellTrans.getValue( considerCommission )
            profitValue = -sellProfit - buyCost
            totalGain += profitValue

            entryDate: datetime.datetime = sellTrans.transTime
            if startDate is not None and entryDate < startDate:
                ## accumulates older values in one entry 'entryDate'
                entryDate = startDate

            if not ret:
                ret.append( [ entryDate, totalGain ] )
                continue
            recentDate = ret[-1][0]
            if entryDate != recentDate:
                ret.append( [ entryDate, totalGain ] )
            else:
                ret[-1][1] = totalGain

        return ret

    ## calculate overall profit (sum of differences between sell and buy values) of made transactions
    ## buy transactions are interpreted as cost
    def transactionsOverallProfit(self):
        profitValue = 0
        for transItem in self.transactions:
            ## positive amount: buy  -- decrease transactions sum
            ## negative amount: sell -- increase transactions sum
            profitValue -= transItem.getValue( True )
        return profitValue

    ## =============================================================

    ## Return list of indexes.
    ## Indicates how many 'stockData' items are before transaction indicated by list index.
    def matchStockBefore(self, stockData ):
        if stockData is None:
            return []
        if stockData.empty:
            return []

        ret = []

        stockValuesFrame = stockData[ ["t", "c"] ]
        stockRowsNum     = stockValuesFrame.shape[0]
        stockRowIndex    = 0

        ## iterate over transactions
        ## calculate values based on transactions and stock price changes
        for nextTrans in reversed( self.transactions ):                           # type: ignore
            transTime = nextTrans.transTime

            counter = 0

            ## iterate over stock historic prices
            while stockRowIndex < stockRowsNum:
                stockTime = stockValuesFrame.at[ stockRowIndex, "t" ]
                if stockTime < transTime:
                    stockRowIndex += 1
                    counter += 1
                else:
                    ## stock time is after transaction time -- break
                    break

            ret.append( counter )

        ret.reverse()
        return ret

    def matchStockAfter(self, stockData):
        indices_list = self.matchStockAfterIndices( stockData )
        stockRowsNum = stockData.shape[0] - 1
        #indices_list.append( stockRowsNum )
        indices_list = [ stockRowsNum ] + indices_list
        counter_list = []
        for i in range(1, len(indices_list)):
            counted = indices_list[i - 1] - indices_list[i]
            counter_list.append( counted )
        return counter_list

    ## Return list of indexes.
    ## Indicates how many 'stockData' items ('t' column) are after transaction indicated by list index.
    ## Returned values in list are indexes of 'stockData'
    ## Can return negative index (-1) meaning that transaction was made before first trading day (presale case)
    def matchStockAfterIndices(self, stockData ):
        if stockData is None:
            return []
        if stockData.empty:
            return []

        ret = []

        stockValuesFrame = stockData[ ["t"] ]
        stockRowsNum     = stockValuesFrame.shape[0]
        stockRowIndex    = stockRowsNum - 1

        ## iterate over transactions
        ## calculate values based on transactions and stock price changes
        for nextTrans in self.transactions:                           # type: ignore
            transTime = nextTrans.transTime

            ## iterate over stock historic prices
            while stockRowIndex > -1:
                stockTime = stockValuesFrame.at[ stockRowIndex, "t" ]
                if stockTime > transTime:
                    stockRowIndex -= 1
                else:
                    ## stock time is after transaction time -- break
                    break

            ret.append( stockRowIndex )

        ## no need to reverse 'ret'
        return ret

    ## calculate profit of single stock
    def calculateValueHistory( self, stockData: DataFrame ) -> DataFrame:
        if stockData is None:
            return None
        if stockData.empty:
            return stockData

        startDateTime = stockData.iloc[0, 0]                        ## first date company in stock exchange
        transStartIndex           = self.findIndex( startDateTime )
        # transBefore: TransHistory
        # pendingTrans: TransHistory
        transBefore, pendingTrans = self.splitTransactions( transStartIndex, True )
        revPending                = pendingTrans[::-1]                           ## reverse list

        stockValuesFrame = stockData[ ["t"] ].copy()
        stockValuesFrame["c"] = 0.0
        rowsNum = stockData.shape[0]

        matchStockIndices = pendingTrans.matchStockAfterIndices( stockValuesFrame )
        matchStockIndices.reverse()

        matchSize = len( matchStockIndices )

        matchStockIndices.append( rowsNum )

        ## iterate over transactions
        ## calculate values based on transactions and stock price changes
        for transIndex in range(0, matchSize):
            nextTrans = revPending[ transIndex ]
            transBefore.appendItem( nextTrans )
            transAmount = transBefore.currentAmount()

            ## iterate over stock historic prices
            rowStartIndex = matchStockIndices[ transIndex ]
            rowStartIndex = max( rowStartIndex, 0 )                 # negative index can occur
            rowEndIndex = matchStockIndices[ transIndex + 1 ]
            for rowIndex in range(rowStartIndex, rowEndIndex):
                sellValue = 0
                if transAmount > 0:
                    stockPrice = stockData.at[ rowIndex, "c" ]
                    sellValue  = stockPrice * transAmount
                    # sellValue -= broker_commission( sellValue )
                stockValuesFrame.at[ rowIndex, "c" ] = sellValue

        ret_data = trim_frame( stockValuesFrame, "c" )
        if ret_data is not None:
            ret_data['t'] = ret_data['t'].apply(lambda x: x.date())
            # ret_data.loc[:,'t'] = ret_data['t'].apply(lambda x: x.date())
        return ret_data

    ## calculate profit of single stock
    def calculateProfitHistory(self, stockData: DataFrame, transMode: TransactionMatchMode,
                               calculateOverall: bool = True) -> DataFrame:
        if stockData is None:
            return None
        if stockData.empty:
            return stockData

        startDateTime = stockData.iloc[0, 0]        ## first date

        transStartIndex           = self.findIndex( startDateTime )
        transBefore, pendingTrans = self.splitTransactions( transStartIndex, True )
        revPending                = pendingTrans[::-1]                           ## reverse list

        stockValuesFrame = stockData[ ["t"] ].copy()
        stockValuesFrame["c"] = 0.0
        rowsNum = stockData.shape[0]

        matchStockIndices = pendingTrans.matchStockAfterIndices( stockValuesFrame )
        matchStockIndices.reverse()

        matchSize = len( matchStockIndices )

        matchStockIndices.append( rowsNum )

        ## iterate over transactions
        ## calculate values based on transactions and stock price changes
        for transIndex in range(0, matchSize):
            nextTrans = revPending[ transIndex ]
            transBefore.appendItem( nextTrans )
            transAmount = transBefore.currentAmount()

            transProfit = 0.0
            if calculateOverall:
                transProfit = transBefore.transactionsOverallProfit()
            else:
                ## cost of stock buy
                buyAmount, buyUnitPrice = transBefore.currentTransactionsAvg( transMode )
                buyValue = buyAmount * buyUnitPrice
                transProfit -= buyValue

            ## iterate over stock historic prices
            rowStartIndex = matchStockIndices[ transIndex ]
            rowStartIndex = max( rowStartIndex, 0 )                 # negative index can occur
            rowEndIndex = matchStockIndices[ transIndex + 1 ]
            # _LOGGER.info( f"cccccccccccccccc: {rowStartIndex} {rowEndIndex} - {matchStockIndices}" )
            for rowIndex in range(rowStartIndex, rowEndIndex):
                sellValue = 0
                if transAmount > 0:
                    ## calculate hypotetical profit if stock would be sold out
                    stockTime  = stockData.at[ rowIndex, "t" ]
                    stockPrice = stockData.at[ rowIndex, "c" ]
                    sellValue  = stockPrice * transAmount
                    sellValue -= broker_commission( sellValue, stockTime )
                profit_value = transProfit + sellValue
                # _LOGGER.info( f"aaaaaaaa: {rowIndex} {stockData.at[ rowIndex, 't' ]} x {transProfit} {sellValue} y {profit_value}" )
                stockValuesFrame.at[ rowIndex, "c" ] = profit_value

        ret_data = trim_frame( stockValuesFrame, "c" )
        if ret_data is not None:
            ret_data['t'] = ret_data['t'].apply(lambda x: x.date())
            # ret_data.loc[:,'t'] = ret_data['t'].apply(lambda x: x.date())
        return ret_data

    def matchTransactions( self, mode: TransactionMatchMode, matchTime: datetime.datetime = None ) -> TransactionsMatch:
        ## Buy value raises then current unit price rises
        ## Sell value raises then current unit price decreases
        sellList = []
        currTransactions = TransHistory()
        ## Transaction
        for item in reversed( self.transactions ):
            transactionTimestamp = item.transTime
            if matchTime is not None and transactionTimestamp > matchTime:
                break
            amount = item.amount
            if amount > 0:
                ## buy transaction
                currTransactions.appendItem( item )
                continue
            ## sell transaction -- match buy transactions
            reducedBuy = currTransactions.reduceTransactions( item, mode )
#             if len( reducedBuy ) < 1:
#                 _LOGGER.info( "invalid reduction: %s %s", item, mode )
#                 pprint( self.transactions )
            for buy in reducedBuy:
                sell = deepcopy( item )
                amountDiff = sell.amount + buy.amount
                sell.reduceAmount( amountDiff )
                pair = ( buy, sell )
                sellList.append( pair )
        walletList = currTransactions.transactions
        return ( walletList, sellList )

    ## current stock in wallet (similar to mb calculation)
    def matchTransactionsFirst(self) -> TransactionsMatch:
        return self.matchTransactions( TransactionMatchMode.OLDEST )

    def matchTransactionsBestFit(self) -> TransactionsMatch:
        return self.matchTransactions( TransactionMatchMode.BEST )

    def matchTransactionsRecentProfit(self) -> TransactionsMatch:
        return self.matchTransactions( TransactionMatchMode.RECENT_PROFIT )

    ## returns reduced buy transactions
    def reduceTransactions(self, sellTransaction: Transaction, mode: TransactionMatchMode) -> BuyTransactionsMatch:
        retList: List[ Transaction ] = []
        amount = -sellTransaction.amount
        while amount > 0:
            bestIndex = self.findMatchingTransaction( sellTransaction, mode )
            if bestIndex < 0:
                ## if this happens then it means there is problem with importing transactions history
                ## perhaps the importer didn't recognized or badly merged transactions
                ## or exported history is not completed (e.g. exported only last year)
                _LOGGER.error( "invalid index %s %s %s", bestIndex, self.size(), len(retList) )
                return retList

            ## reduce amount
            bestItem: Transaction = self.transactions[ bestIndex ]
            bestAmount = bestItem.amount
            amountDiff = bestAmount - amount
            if amountDiff > 0:
                bestCopied = deepcopy( bestItem )
                bestCopied.reduceAmount( amountDiff )
                retList.append( bestCopied )
                bestItem.reduceAmount( amount )
                return retList

            ## bestAmount <= amount
            amount -= bestAmount
            retList.append( self.transactions[ bestIndex ] )
            del self.transactions[ bestIndex ]

        if amount > 0:
            _LOGGER.warning( "invalid case %s", amount )
        return retList

    def findMatchingTransaction( self, sellTransaction: Transaction, mode: TransactionMatchMode ):
        if mode is TransactionMatchMode.OLDEST:
            return len( self.transactions ) - 1
        if mode is TransactionMatchMode.BEST:
            return self.findCheapest()
        if mode is TransactionMatchMode.RECENT_PROFIT:
            return self.findMatchingRecentProfit( sellTransaction )

        _LOGGER.warning("mode not handled: %s, cheapest returned", mode)
        return self.findCheapest()

    def findCheapest(self):
        cSize = self.size()
        if cSize < 1:
            return -1
        bestIndex = 0
        bestPrice = self.transactions[0].unitPrice
        for i in range(1, cSize):
            currPrice = self.transactions[i].unitPrice
            if currPrice < bestPrice:
                bestPrice = currPrice
                bestIndex = i
        return bestIndex

    def findMatchingRecentProfit( self, sellTransaction: Transaction ):
        cSize = self.size()
        if cSize < 1:
            return -1
        sellPrice = sellTransaction.unitPrice
        for i in range(0, cSize):
            item = self.transactions[i]
            if item.amount < 1:
                ## sell transaction -- ignore
                continue
            if item.unitPrice < sellPrice:
                ## recent profit found -- return
                return i
        ## no cheaper found -- find best
        return self.findCheapest()

    def _findSame(self, unit_price, trans_date, amount, commission):
#         for i in range( len( self.transactions ) ):
        for i, item in enumerate( self.transactions ):
            itemAmount, itemPrice, itemCommission, itemTime = item
            if itemAmount != amount:
                continue
            if itemPrice != unit_price:
                continue
            if itemCommission != commission:
                continue
            if itemTime != trans_date:
                continue
            return i
        return -1

    def _findSimilar(self, unit_price, trans_date):
#         for i in range( len( self.transactions ) ):
#             item = self.transactions[i]
        for i, item in enumerate( self.transactions ):
            if item.unitPrice != unit_price:
                continue
            diff = item.transTime - trans_date
            # print("diff:", item[2], trans_date, diff)
            if -datetime.timedelta( minutes=5 ) < diff < datetime.timedelta( minutes=5 ):
                return i
        return -1

    def sort(self):
        self.transactions.sort( key=Transaction.sortKey, reverse=True )


## =======================================================


def broker_commission( value, transTime=None ):
    ## always returns positive value
    minCommission = 3.0
    if transTime is None:
        transTime = datetime.datetime.today().date()
    elif isinstance(transTime, datetime.datetime):
        transTime = transTime.date()

    if transTime > datetime.date( year=2020, month=10, day=6 ):
        minCommission = 5.0
    commission = abs( value ) * 0.0039
    commission = max( commission, minCommission )
    return commission


def trim_frame( stockValuesFrame, column_name ):
    numeric_data = stockValuesFrame.loc[:, column_name].values
    non_zero_index = numpy.argmax(numeric_data != 0, axis=0)
    if non_zero_index == 0:
        # it means that first row is non-zero or no row found
        if numeric_data[non_zero_index] == 0:
            # no non-zero data found - nothing to add
            return None
        return stockValuesFrame

    # return non-zero data
    ret_data = stockValuesFrame.iloc[non_zero_index:]
    ret_data.reset_index( drop=True, inplace=True )
    return ret_data
