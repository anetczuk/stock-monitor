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
from datetime import datetime, date, timedelta

from typing import Dict, List, Tuple

from stockmonitor import persist


_LOGGER = logging.getLogger(__name__)


## amount, unit_price, transaction time
Transaction = Tuple[int, float, datetime]

BuyTransactionsMatch  = List[ Transaction ]
SellTransactionsMatch = List[ Tuple[Transaction, Transaction] ]
TransactionsMatch     = Tuple[ BuyTransactionsMatch, SellTransactionsMatch ]


@unique
class TransactionMatchMode(Enum):
    OLDEST = ()
    BEST = ()
    RECENT_PROFIT = ()

    def __new__(cls):
        value = len(cls.__members__)  # note no + 1
        obj = object.__new__(cls)
        # pylint: disable=W0212
        obj._value_ = value
        return obj


class TransHistory():

    def __init__(self):
        ## most recent transaction on top (with index 0)
        self.transactions: List[ Transaction ] = list()

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
            stockAmount += item[0]
        return stockAmount

    def amountBeforeDate(self, transDate):
        stockAmount = 0
        for item in self.transactions:
            itemDate = item[2].date()
            if itemDate < transDate:
                stockAmount += item[0]
        return stockAmount

    def append(self, amount, unitPrice, transTime: datetime=None):
        self.transactions.insert( 0, (amount, unitPrice, transTime) )

    def appendItem(self, item):
        self.transactions.insert( 0, (item[0], item[1], item[2]) )

    def appendList(self, itemList):
        for item in itemList:
            self.appendItem( item )
        self.sort()

    def add(self, amount, unitPrice, transTime=None, joinSimilar=True):
        if joinSimilar is False:
#                 _LOGGER.debug( "adding transaction: %s %s %s", amount, unitPrice, transTime )
            self.append( amount, unitPrice, transTime )
            self.sort()
            return
        sameIndex = self._findSame( unitPrice, transTime, amount )
        if sameIndex > -1:
            return
        similarIndex = self._findSimilar( unitPrice, transTime )
        if similarIndex < 0:
#                 _LOGGER.debug( "adding transaction: %s %s %s", amount, unitPrice, transTime )
            self.append( amount, unitPrice, transTime )
            self.sort()
            return
        _LOGGER.debug( "joining transaction: %s %s %s", amount, unitPrice, transTime )
        self.addAmount( similarIndex, amount )

    def addAmount(self, index, value):
        item = self.transactions[ index ]
        newAmount = item[0] + value
        self.transactions[ index ] = ( newAmount, item[1], item[2] )

    ## =============================================================

#     def calcAvg(self):
#         ## Buy value raises then current unit price rises
#         ## Sell value raises then current unit price decreases
#         currAmount = 0
#         currValue  = 0
#
#         for amount, unit_price, _ in self.transactions:
#             currAmount += amount
#             currValue  += amount * unit_price
#
#         if currAmount == 0:
#             ## ignore no wallet stock transaction
#             return (0, 0)
#
#         currUnitPrice = currValue / currAmount
#         return ( currAmount, currUnitPrice )

    ## calculate overall profit of made transactions
    def transactionsProfit(self, considerCommission=True):
        profitValue = 0
        for amount, unit_price, transTime in self.transactions:
            ## positive amount: buy  -- decrease transactions sum
            ## negative amount: sell -- increase transactions sum
            currValue = amount * unit_price
            profitValue -= currValue
            if considerCommission:
                commission = broker_commission( currValue, transTime )
                profitValue -= commission
        return profitValue

    def transactionsAfter(self, startDate) -> 'TransHistory':
        transList = list()
        for item in self.transactions:
            transTime = item[2]
            transDate = transTime.date()
            if transDate < startDate:
                continue
            transList.append( item )
        retTrans = TransHistory()
        retTrans.appendList( transList )
        return retTrans

    def transactionsBefore(self, endDate) -> 'TransHistory':
        transList = list()
        for item in self.transactions:
            transTime = item[2]
            transDate = transTime.date()
            if transDate < endDate:
                transList.append( item )
        retTrans = TransHistory()
        retTrans.appendList( transList )
        return retTrans

    ## buy transactions in wallet
    def currentTransactions( self, mode: TransactionMatchMode ) -> BuyTransactionsMatch:
        retPair = self.matchTransactions( mode )
        return retPair[0]

    ## average value of current amount of stock
    ## returns pair: (amount, unit_price)
    def currentTransactionsAvg(self, mode: TransactionMatchMode):
        ## Buy value raises then current unit price rises
        ## Sell value raises then current unit price decreases

        transList = self.currentTransactions( mode )
        if not transList:
            return (0, 0)

        currAmount = 0
        currValue  = 0.0
        for transItem in transList:
            amount     = transItem[0]
            unit_price = transItem[1]
            currAmount += amount
            currValue  += amount * unit_price

        currUnitPrice = currValue / currAmount
        return ( currAmount, currUnitPrice )

    ## returns List[ (buy transaction, sell transaction) ]
    def sellTransactions(self, mode: TransactionMatchMode) -> SellTransactionsMatch:
        retPair = self.matchTransactions( mode )
        return retPair[1]

    def transactionsGain(self, mode: TransactionMatchMode, considerCommission=True):
        totalGain = 0.0
        sellTransactions: SellTransactionsMatch = self.sellTransactions( mode )
        for buyTrans, sellTrans in sellTransactions:
            buyAmount, buyPrice, buyDate = buyTrans
            sellAmount, sellPrice, sellDate = sellTrans
            buyCost    = buyAmount * buyPrice
            sellProfit = sellAmount * sellPrice
            profitValue = -sellProfit - buyCost
            if considerCommission:
                buyCommission = broker_commission( buyCost, buyDate )
                profitValue -= buyCommission
                sellCommission = broker_commission( sellProfit, sellDate )
                profitValue -= sellCommission
            totalGain += profitValue
        return totalGain

    def matchTransactions( self, mode: TransactionMatchMode ) -> TransactionsMatch:
        ## Buy value raises then current unit price rises
        ## Sell value raises then current unit price decreases
        sellList = list()
        currTransactions = TransHistory()
        for item in reversed( self.transactions ):
            amount = item[0]
            if amount > 0:
                currTransactions.appendItem( item )
                continue
            reducedBuy = currTransactions.reduceTransactions( item, mode )
            for buy in reducedBuy:
                sell = ( -buy[0], item[1], item[2] )
                pair = ( buy, sell )
                sellList.append( pair )
        walletList = currTransactions.transactions
        return ( walletList, sellList )

    ## current stock in wallet (similar to mb calculation)
    def matchTransactionsRecent(self) -> TransactionsMatch:
        return self.matchTransactions( TransactionMatchMode.OLDEST )

    def matchTransactionsBestFit(self) -> TransactionsMatch:
        return self.matchTransactions( TransactionMatchMode.BEST )

    def matchTransactionsRecentProfit(self) -> TransactionsMatch:
        return self.matchTransactions( TransactionMatchMode.RECENT_PROFIT )

    ## returns reduced buy transactions
    def reduceTransactions(self, sellTransaction: Transaction, mode: TransactionMatchMode) -> BuyTransactionsMatch:
        retList: List[ Transaction ] = []
        amount = -sellTransaction[0]
        while amount > 0:
            bestIndex = self.findMatchingTransaction( sellTransaction, mode )
            if bestIndex < 0:
                ## if this happens then it means there is problem with importing transactions history
                ## perhaps the importer didn't recognized or badly merged transactions
                _LOGGER.error( "invalid index %s %s", bestIndex, self.size() )
                return retList

            ## reduce amount
            bestItem = self.transactions[ bestIndex ]
            if bestItem[0] > amount:
                self.addAmount(bestIndex, -amount)
                unit_price = bestItem[1]
                trans_time = bestItem[2]
                retList.append( ( amount, unit_price, trans_time ) )
                return retList

            ## bestItem[0] <= amount
            amount -= bestItem[0]
            retList.append( self.transactions[ bestIndex ] )
            del self.transactions[ bestIndex ]

        if amount > 0:
            _LOGGER.warning( "invalid case %s", amount )
        return retList

#         if mode is TransactionMatchMode.OLDEST:
#             return self.reduceOldest( amount )
#         elif mode is TransactionMatchMode.BEST:
#             return self.reduceCheapest( amount )
#         elif mode is TransactionMatchMode.RECENT_PROFIT:
#             return self.reduceRecentProfit( amount )
#
#         _LOGGER.warning("mode not handled: %s, best fit returned", mode)
#         return self.reduceCheapest( amount )

#     ## returns reduced buy transactions
#     def reduceOldest(self, amount) -> BuyTransactionsMatch:
#         retList: List[ Transaction ] = []
#         while amount > 0:
#             if len( self.transactions ) < 1:
#                 ## if this happens then it means there is problem with importing transactions history
#                 ## perhaps the importer didn't recognized or badly merged transactions
#                 _LOGGER.error( "empty transactions" )
#                 return retList
#             bestIndex = -1
#
#             ## reduce amount
#             bestItem = self.transactions[ bestIndex ]
#             if bestItem[0] > amount:
#                 self.addAmount(bestIndex, -amount)
#                 unit_price = bestItem[1]
#                 trans_time = bestItem[2]
#                 retList.append( ( amount, unit_price, trans_time ) )
#                 return retList
#
#             ## bestItem[0] <= amount
#             amount -= bestItem[0]
#             retList.append( self.transactions[ bestIndex ] )
#             del self.transactions[ bestIndex ]
#
#         if amount > 0:
#             _LOGGER.warning( "invalid case %s", amount )
#         return retList
#
#     ## returns reduced buy transactions
#     def reduceCheapest(self, amount) -> BuyTransactionsMatch:
#         retList: List[ Transaction ] = []
#         while amount > 0:
#             bestIndex = self.findCheapest()
#             if bestIndex < 0:
#                 ## if this happens then it means there is problem with importing transactions history
#                 ## perhaps the importer didn't recognized or badly merged transactions
#                 _LOGGER.error( "invalid index %s %s", bestIndex, self.size() )
#                 return retList
#
#             ## reduce amount
#             bestItem = self.transactions[ bestIndex ]
#             if bestItem[0] > amount:
#                 self.addAmount(bestIndex, -amount)
#                 unit_price = bestItem[1]
#                 trans_time = bestItem[2]
#                 retList.append( ( amount, unit_price, trans_time ) )
#                 return retList
#
#             ## bestItem[0] <= amount
#             amount -= bestItem[0]
#             retList.append( self.transactions[ bestIndex ] )
#             del self.transactions[ bestIndex ]
#
#         if amount > 0:
#             _LOGGER.warning( "invalid case %s", amount )
#         return retList
#
#     ## returns reduced buy transactions
#     def reduceRecentProfit(self, amount) -> BuyTransactionsMatch:
#         #TODO: implement
#         return []
# #         retList: List[ Transaction ] = []
# #         while amount > 0:
# #             bestIndex = self.findCheapest()
# #             if bestIndex < 0:
# #                 ## if this happens then it means there is problem with importing transactions history
# #                 ## perhaps the importer didn't recognized or badly merged transactions
# #                 _LOGGER.error( "invalid index %s %s", bestIndex, self.size() )
# #                 return retList
# #             ## reduce amount
# #             bestItem = self.transactions[ bestIndex ]
# #             if bestItem[0] > amount:
# #                 self.addAmount(bestIndex, -amount)
# #                 unit_price = bestItem[1]
# #                 trans_time = bestItem[2]
# #                 retList.append( ( amount, unit_price, trans_time ) )
# #                 return retList
# #
# #             ## bestItem[0] <= amount
# #             amount -= bestItem[0]
# #             retList.append( self.transactions[ bestIndex ] )
# #             del self.transactions[ bestIndex ]
# #
# #         if amount > 0:
# #             _LOGGER.warning( "invalid case %s", amount )
# #         return retList

    def findMatchingTransaction( self, sellTransaction: Transaction, mode: TransactionMatchMode ):
        if mode is TransactionMatchMode.OLDEST:
            return len( self.transactions ) - 1
        elif mode is TransactionMatchMode.BEST:
            return self.findCheapest()
        elif mode is TransactionMatchMode.RECENT_PROFIT:
            return self.findMatchingRecentProfit( sellTransaction )

        _LOGGER.warning("mode not handled: %s, cheapest returned", mode)
        return self.findCheapest()

    def findCheapest(self):
        cSize = self.size()
        if cSize < 1:
            return -1
        bestIndex = 0
        bestPrice = self.transactions[0][1]
        for i in range(1, cSize):
            currPrice = self.transactions[i][1]
            if currPrice < bestPrice:
                bestPrice = currPrice
                bestIndex = i
        return bestIndex

    def findMatchingRecentProfit( self, sellTransaction: Transaction ):
        cSize = self.size()
        if cSize < 1:
            return -1
        sellPrice = sellTransaction[1]
        for i in range(0, cSize):
            item = self.transactions[i]
            if item[0] < 1:
                ## sell transaction -- ignore
                continue
            if item[1] < sellPrice:
                ## recent profit found -- return
                return i
        ## no cheaper found -- find best
        return self.findCheapest()

    def _findSame(self, unit_price, trans_date, amount):
        for i in range( len( self.transactions ) ):
            itemAmount, itemPrice, itemTime = self.transactions[i]
            if itemAmount != amount:
                continue
            if itemPrice != unit_price:
                continue
            if itemTime != trans_date:
                continue
            return i
        return -1

    def _findSimilar(self, unit_price, trans_date):
        for i in range( len( self.transactions ) ):
            item = self.transactions[i]
            if item[1] != unit_price:
                continue
            diff = item[2] - trans_date
            # print("diff:", item[2], trans_date, diff)
            if diff < timedelta( minutes=5 ) and diff > -timedelta( minutes=5 ):
                return i
        return -1

    def sort(self):
        self.transactions.sort( key=self._sortKey, reverse=True )

    @staticmethod
    def _sortDate( tuple1, tuple2 ):
        date1 = tuple1[2]
        if date1 is None:
            return 1
        date2 = tuple2[2]
        if date2 is None:
            return -1
        return date1 < date2

    @staticmethod
    def _sortKey( tupleValue ):
        retDate = tupleValue[2]
        if retDate is None:
            return datetime.min
        return retDate


## =======================================================


class WalletData( persist.Versionable ):

    ## 0 - first version
    ## 1 - dict instead of list
    ## 2 - sort transactions
    _class_version = 2

    def __init__(self):
        ## ticker, TransHistory
        self.stockList: Dict[ str, TransHistory ] = dict()

    def _convertstate_(self, dict_, dictVersion_ ):
        _LOGGER.info( "converting object from version %s to %s", dictVersion_, self._class_version )

        if dictVersion_ is None:
            dictVersion_ = 0

        if dictVersion_ < 0:
            ## nothing to do
            dictVersion_ = 0

        if dictVersion_ == 0:
            dict_["stockList"] = dict()
            dictVersion_ = 1

        if dictVersion_ == 1:
            histDict = dict_["stockList"]
            for _, item in histDict.items():
                item.sort()
            dictVersion_ = 2

        # pylint: disable=W0201
        self.__dict__ = dict_

    def __getitem__(self, ticker) -> TransHistory:
        return self.stockList.get( ticker, None )

    def size(self):
        return len( self.stockList )

    def clear(self):
        self.stockList.clear()

    def tickers(self):
        return self.stockList.keys()

    def transactions(self, ticker) -> TransHistory:
        return self.stockList.get( ticker, None )

    ## returns List[ (ticker, curr amount, avg unit price) ]
    def currentItems( self, mode: TransactionMatchMode ) -> List[ Tuple[str, int, float] ]:
        ret: List[ Tuple[str, int, float] ] = list()
        for key, hist in self.stockList.items():
            if key is None:
                _LOGGER.warning("found wallet None key")
                continue
            val = hist.currentTransactionsAvg( mode )     # pair: (amount, unit_price)
            if val is not None:
                ret.append( (key, val[0], val[1]) )
        return ret

    def add( self, ticker, amount, unitPrice, transTime: datetime=datetime.today(), joinSimilar=True ):
        transactions: TransHistory = self.stockList.get( ticker, None )
        if transactions is None:
            transactions = TransHistory()
            self.stockList[ ticker ] = transactions
        _LOGGER.debug( "adding transaction: %s %s %s %s", ticker, amount, unitPrice, transTime )
        transactions.add( amount, unitPrice, transTime, joinSimilar )

    def addTransaction( self, ticker, transaction: Transaction, joinSimilar=True ):
        self.add( ticker, transaction[0], transaction[1], transaction[2], joinSimilar )

    def addWallet(self, wallet: 'WalletData', joinSimilar=True):
        for ticker, hist in wallet.stockList.items():
            for trans in hist.transactions:
                self.addTransaction(ticker, trans, joinSimilar)

    def getCurrentStock(self) -> List[ str ]:
        ret = list()
        for key, hist in self.stockList.items():
            amount = hist.currentAmount()
            if amount > 0:
                ret.append( key )
        return ret


def broker_commission( value, transTime=None ):
    ## always returns positive value
    minCommission = 3.0
    if transTime is None:
        transTime = datetime.today().date()
    elif isinstance(transTime, datetime):
        transTime = transTime.date()

    if transTime > date( year=2020, month=10, day=6 ):
        minCommission = 5.0
    commission = abs( value ) * 0.0039
    commission = max( commission, minCommission )
    return commission
