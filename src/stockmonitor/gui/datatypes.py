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

import logging
import collections
import glob
from datetime import datetime, date, timedelta

from typing import Dict, List, Tuple

from stockmonitor import persist
from stockmonitor.dataaccess.gpw.gpwintradaydata import GpwCurrentIndexIntradayData,\
    GpwCurrentStockIntradayData


_LOGGER = logging.getLogger(__name__)


class FavData( persist.Versionable ):

    ## 0 - first version
    ## 1 - use ordererd dict
    ## 2 - use favs set
    ## 3 - use favs group list
    ## 4 - remove redundant field
    ## 5 - restore favs group as ordered dict
    ## 6 - use favs list
    _class_version = 6

    def __init__(self):
        ## Use list internally. For unknown reason Set causes persist to
        ## detect changes (difference in file content) even if elements does not change.
        self.favsList: Dict[ str, List[str] ] = collections.OrderedDict()

    def _convertstate_(self, dict_, dictVersion_ ):
        _LOGGER.info( "converting object from version %s to %s", dictVersion_, self._class_version )

        if dictVersion_ is None:
            dictVersion_ = -1

        if dictVersion_ < 0:
            ## nothing to do
            dictVersion_ = 0

        if dictVersion_ == 0:
            ## use ordererd dict
            oldDict = dict_["favs"]
            newDict = collections.OrderedDict( oldDict )
            dict_["favs"] = newDict
            dictVersion_ = 1

        if dictVersion_ == 1:
            ## use ordererd dict
            favsDict = dict_["favs"]
            for key in favsDict.keys():
                favsDict[key] = set( favsDict[key] )
            dict_["favs"] = favsDict
            dictVersion_ = 2

        if dictVersion_ == 2:
            ## convert ordererd dict to list
            favsDict = dict_["favs"]
            favsList = list()
            for key in favsDict.keys():
                pair = ( key, favsDict[key] )
                favsList.append( pair )
            del dict_["favs"]
            dict_["favsList"] = favsList
            dictVersion_ = 3

        if dictVersion_ == 3:
            ## remove redundant field
            if "favs" in dict_.keys():
                del dict_["favs"]
            dictVersion_ = 4

        if dictVersion_ == 4:
            favsList = dict_["favsList"]
            favsDict = collections.OrderedDict()
            for item in favsList:
                grp = item[0]
                favsDict[ grp ] = item[1]
            dict_["favsList"] = favsDict
            dictVersion_ = 5

        if dictVersion_ == 5:
            favsDict = dict_["favsList"]
            for key in favsDict.keys():
                favsDict[ key ] = list( favsDict[ key ] )
            dict_["favsList"] = favsDict
            dictVersion_ = 6

        # pylint: disable=W0201
        self.__dict__ = dict_

    def containsGroup(self, group):
        found = self.getFavs( group )
        return found is not None

    def getFavGroups(self):
        return self.favsList.keys()

    def getFavs(self, group) -> List[str]:
        return self.favsList.get( group, None )

    def getFavsAll(self):
        ret = set()
        for val in self.favsList.values():
            ret = ret | set( val )
        return ret

    def addFavGroup(self, name):
        if name not in self.favsList:
            self.favsList[name] = list()

    def renameFavGroup(self, fromName, toName):
#         self.favsList[toName] = self.favsList.pop(fromName)
        dLen = len(self.favsList)
        for _ in range(dLen):
            k, v = self.favsList.popitem(False)
            newKey = toName if fromName == k else k
            self.favsList[ newKey ] = v

    def deleteFavGroup(self, name):
        del self.favsList[name]

    def reorderFavGroups(self, newOrder):
        for item in reversed(newOrder):
            # pylint: disable=E1101
            self.favsList.move_to_end( item, False )

    def setFavs(self, group, items):
        itemsList = list( items )
        self.addFavGroup( group )
        newSet = set( itemsList )
        self.favsList[group] = list( newSet )

    def addFav(self, group, items):
        itemsList = list( items )
        self.addFavGroup( group )
        newSet = set( self.favsList[group] + itemsList )          ## sum of sets
        self.favsList[group] = list( newSet )

    def deleteFav(self, group, items):
        _LOGGER.info( "Removing favs: %s from group %s", items, group )
        itemsList = set( items )
        if group not in self.favsList:
            _LOGGER.warning("Unable to find group")
            return
        groupList = self.favsList[group]
        for item in itemsList:
            groupList.remove( item )
        self.favsList[group] = groupList


## =======================================================


class TransHistory():

    def __init__(self):
        ## amount, unit_price, transaction time
        ## most recent transaction on top (with index 0)
        self.transactions: List[ Tuple[int, float, datetime] ] = list()

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

    def calcAvg(self):
        ## Buy value raises then current unit price rises
        ## Sell value raises then current unit price decreases
        currAmount = 0
        currValue  = 0

        for amount, unit_price, _ in self.transactions:
            currAmount += amount
            currValue  += amount * unit_price

        if currAmount == 0:
            ## ignore no wallet stock transaction
            return (0, 0)

        currUnitPrice = currValue / currAmount
        return ( currAmount, currUnitPrice )

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

    def currentTransactions(self):
        return self.currentTransactionsBestFit()
#         return self.currentTransactionsRecent()

    ## current stock in wallet (similar to mb calculation)
    def currentTransactionsRecent(self) -> List[ Tuple[int, float, datetime] ]:
        ## Buy value raises then current unit price rises
        ## Sell value raises then current unit price decreases

        stockAmount = self.currentAmount()
        if stockAmount <= 0:
            ## ignore no wallet stock transaction
            return []

        retList = TransHistory()

        currAmount = 0
        for item in self.transactions:
            amount = item[0]
            if amount <= 0:
                ## ignore sell transaction
                continue

            currAmount += amount

            amountDiff = currAmount - stockAmount
            if amountDiff > 0:
                restAmount = amount - amountDiff
                if restAmount <= 0:
                    break
                amount = restAmount

            retList.append( amount, item[1], item[2] )

        return retList.items()

    def currentTransactionsBestFit(self) -> List[ Tuple[int, float, datetime] ]:
        ## Buy value raises then current unit price rises
        ## Sell value raises then current unit price decreases
        currTransactions = TransHistory()
        for item in reversed( self.transactions ):
            amount = item[0]
            if amount > 0:
                currTransactions.appendItem( item )
                continue
            currTransactions.reduceCheapest( -amount )
        return currTransactions.transactions

    ## average value of current amount of stock
    def currentTransactionsAvg(self):
        ## Buy value raises then current unit price rises
        ## Sell value raises then current unit price decreases

        transList = self.currentTransactions()
        if not transList:
            return (0, 0)

        currAmount = 0
        currValue  = 0
        for transItem in transList:
            amount     = transItem[0]
            unit_price = transItem[1]
            currAmount += amount
            currValue  += amount * unit_price

        currUnitPrice = currValue / currAmount
        return ( currAmount, currUnitPrice )

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

    def transactionsBefore(self, endtDate) -> 'TransHistory':
        transList = list()
        for item in self.transactions:
            transTime = item[2]
            transDate = transTime.date()
            if transDate < endtDate:
                transList.append( item )
        retTrans = TransHistory()
        retTrans.appendList( transList )
        return retTrans

    def reduceCheapest(self, amount):
        while amount > 0:
            bestIndex = self.findCheapest()
            if bestIndex < 0:
                _LOGGER.warning( "invalid index %s", bestIndex )
                return
            ## reduce amount
            bestItem = self.transactions[ bestIndex ]
            if bestItem[0] > amount:
                self.addAmount(bestIndex, -amount)
                return

            ## bestItem[0] <= amount
            amount -= bestItem[0]
            del self.transactions[ bestIndex ]

        if amount > 0:
            _LOGGER.warning( "invalid case %s", amount )

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
        ## ticker, amount, unit price
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

    def transactions(self, ticker) -> TransHistory:
        return self.stockList.get( ticker, None )

    def items(self) -> List[ Tuple[str, int, float] ]:
        ret = list()
        for key, hist in self.stockList.items():
            if key is None:
                _LOGGER.warning("found wallet None key")
                continue
            val = hist.currentTransactionsAvg()
            if val is not None:
                ret.append( (key, val[0], val[1]) )
        return ret

    def add( self, ticker, amount, unitPrice, transTime: datetime=datetime.today(), joinSimilar=True ):
        transactions = self.stockList.get( ticker, None )
        if transactions is None:
            transactions = TransHistory()
            self.stockList[ ticker ] = transactions
        _LOGGER.debug( "adding transaction: %s %s %s %s", ticker, amount, unitPrice, transTime )
        transactions.add( amount, unitPrice, transTime, joinSimilar )

    def getCurrentStock(self) -> List[ str ]:
        ret = list()
        for key, hist in self.stockList.items():
            amount = hist.currentAmount()
            if amount > 0:
                ret.append( key )
        return ret


class UserContainer():

    ## 0 - first version
    ## 1 - wallet added
    ## 2 - extract History class from WalletData
    _class_version = 2

    def __init__(self):
        self.favs   = FavData()
        self.notes  = { "notes": "" }        ## default notes
        self.wallet = WalletData()

    def store( self, outputDir ):
        changed = False

        outputFile = outputDir + "/version.obj"
        if persist.store_object( self._class_version, outputFile ) is True:
            changed = True

        outputFile = outputDir + "/favs.obj"
        if persist.store_object( self.favs, outputFile ) is True:
            changed = True

        outputFile = outputDir + "/notes.obj"
        if persist.store_object( self.notes, outputFile ) is True:
            changed = True

        outputFile = outputDir + "/wallet.obj"
        if persist.store_object( self.wallet, outputFile ) is True:
            changed = True

        ## backup data
        objFiles = glob.glob( outputDir + "/*.obj" )
        storedZipFile = outputDir + "/data.zip"
        persist.backup_files( objFiles, storedZipFile )

        return changed

    def load( self, inputDir ):
        inputFile = inputDir + "/version.obj"
        mngrVersion = persist.load_object( inputFile, self._class_version )
        if mngrVersion != self. _class_version:
            _LOGGER.info( "converting object from version %s to %s", mngrVersion, self._class_version )
            ## do nothing for now

        inputFile = inputDir + "/favs.obj"
        self.favs = persist.load_object( inputFile, self._class_version )
        if self.favs is None:
            self.favs = FavData()

        inputFile = inputDir + "/notes.obj"
        self.notes = persist.load_object( inputFile, self._class_version )
        if self.notes is None:
            self.notes = { "notes": "" }

        inputFile = inputDir + "/wallet.obj"
        self.wallet = persist.load_object( inputFile, self._class_version )
        if self.wallet is None:
            self.wallet = WalletData()


## =========================================================================


class StockData():

    def __init__( self, data: object = None ):
        self.stockData                       = data
        self.stockHeaders: Dict[ int, str ]  = dict()

    @property
    def headers(self) -> Dict[ int, str ]:
        return self.stockHeaders

    def refreshData(self, forceRefresh=True):
        self.stockData.refreshData( forceRefresh )

    def loadWorksheet(self, forceRefresh=False):
        self.stockData.loadWorksheet( forceRefresh )

    def downloadData(self):
        self.stockData.downloadData()


class GpwStockIntradayMap():

    def __init__(self):
        self.dataDict = dict()

    def getData(self, isin):
        source = self.getSource(isin)
        return source.getWorksheet()

    def getSource(self, isin, rangeCode=None):
        if rangeCode is None:
            rangeCode = "1D"
        key = isin + "-" + rangeCode
        source = self.dataDict.get( key, None )
        if source is not None:
            return source
        source = GpwCurrentStockIntradayData( isin, rangeCode )
        self.dataDict[ key ] = source
        return source

    def set(self, isin, source):
        self.dataDict[ isin ] = source

    def refreshData(self, forceRefresh=True):
        for val in self.dataDict.values():
            val.refreshData( forceRefresh )


class GpwIndexIntradayMap():

    def __init__(self):
        self.dataDict = dict()

    def getData(self, isin):
        source = self.getSource(isin)
        return source.getWorksheet()

    def getSource(self, isin, rangeCode=None) -> GpwCurrentIndexIntradayData:
        if rangeCode is None:
            rangeCode = "1D"
        key = isin + "-" + rangeCode
        source = self.dataDict.get( key, None )
        if source is not None:
            return source
        source = GpwCurrentIndexIntradayData( isin, rangeCode )
        self.dataDict[ key ] = source
        return source

    def set(self, isin, source):
        self.dataDict[ isin ] = source

    def refreshData(self, forceRefresh=True):
        for val in self.dataDict.values():
            val.refreshData( forceRefresh )


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
