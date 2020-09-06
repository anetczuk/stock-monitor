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
from typing import Dict, List, Tuple
# from multiprocessing import Process, Queue
# from multiprocessing import Pool

from datetime import datetime, timedelta

from pandas.core.frame import DataFrame

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QUndoStack

from stockmonitor import persist
from stockmonitor.dataaccess.datatype import CurrentDataType
from stockmonitor.dataaccess.gpwdata import GpwCurrentData, GpwIsinMapData,\
    GpwCurrentIntradayData
from stockmonitor.dataaccess.gpwdata import GpwIndexesData
from stockmonitor.dataaccess.gpwdata import GpwIndicatorsData
from stockmonitor.dataaccess.dividendsdata import DividendsCalendarData
from stockmonitor.dataaccess.finreportscalendardata import PublishedFinRepsCalendarData, FinRepsCalendarData

import stockmonitor.gui.threadlist as threadlist
from stockmonitor.gui.command.addfavgroupcommand import AddFavGroupCommand
from stockmonitor.gui.command.deletefavgroupcommand import DeleteFavGroupCommand
from stockmonitor.gui.command.renamefavgroupcommand import RenameFavGroupCommand
from stockmonitor.gui.command.addfavcommand import AddFavCommand
from stockmonitor.gui.command.deletefavcommand import DeleteFavCommand
from stockmonitor.gui.command.reorderfavgroupscommand import ReorderFavGroupsCommand
from stockmonitor.dataaccess.globalindexesdata import GlobalIndexesData


_LOGGER = logging.getLogger(__name__)


## ============================================================


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


class WalletData( persist.Versionable ):

    class History():

        def __init__(self):
            ## amount, unit_price, transaction time
            self.transactions: List[ Tuple[int, float, datetime] ] = list()

        def size(self):
            return len( self.transactions )

        def clear(self):
            self.transactions.clear()

        def items(self):
            return self.transactions

        def add(self, amount, unitPrice, transTime=None, joinSimilar=True):
            if joinSimilar is False:
#                 _LOGGER.debug( "adding transaction: %s %s %s", amount, unitPrice, transTime )
                self.transactions.append( (amount, unitPrice, transTime) )
                self.sort()
                return
            similarIndex = self._findSimilar( unitPrice, transTime )
            if similarIndex < 0:
#                 _LOGGER.debug( "adding transaction: %s %s %s", amount, unitPrice, transTime )
                self.transactions.append( (amount, unitPrice, transTime) )
                self.sort()
                return
            _LOGGER.debug( "joining transaction: %s %s %s", amount, unitPrice, transTime )
            similar = self.transactions[ similarIndex ]
            newAmount = similar[0] + amount
            self.transactions[ similarIndex ] = ( newAmount, similar[1], similar[2] )

        def sort(self):
            ## sort by date -- recent date first
#             def sort_alias(a, b):
#                 return self._sortDate(a, b)
#             compare = functools.cmp_to_key( self._sortDate )
# #             compare = functools.cmp_to_key( sort_alias )
# #             self.transactions.sort( key=sort_alias, reverse=True )
#             self.transactions = sorted( self.transactions, key=compare, reverse=True )
# #             self.transactions.sort(key=lambda x: (x[2] is None, x[2]), reverse=True)
            self.transactions.sort( key=self._sortKey, reverse=True )

        def currentAmount(self):
            stockAmount = 0
            for item in self.transactions:
                stockAmount += item[0]
            return stockAmount

        def transactionsProfit(self, considerCommission=True):
            profitValue = 0
            for amount, unit_price, _ in self.transactions:
                ## positive amount: buy  -- decrease transactions sum
                ## negative amount: sell -- increase transactions sum
                currValue = amount * unit_price
                profitValue -= currValue
                if considerCommission:
                    commission = broker_commission( currValue )
                    profitValue -= commission
            return profitValue

        def calc(self):
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

        def currentTransactions(self):
            ## Buy value raises then current unit price rises
            ## Sell value raises then current unit price decreases
            stockAmount = 0

            for item in self.transactions:
                stockAmount += item[0]

            retList = []

            if stockAmount <= 0:
                ## ignore no wallet stock transaction
                return retList

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

                row = list( item )
                row[0] = amount
                retList.append( tuple( row ) )

            return retList

        def calc2(self):
            ## Buy value raises then current unit price rises
            ## Sell value raises then current unit price decreases
            stockAmount = 0

            for item in self.transactions:
                stockAmount += item[0]

            if stockAmount <= 0:
                ## ignore no wallet stock transaction
                return (0, 0)

            currAmount = 0
            currValue  = 0
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

                unit_price = item[1]
                currValue += amount * unit_price

            currUnitPrice = currValue / stockAmount
            return ( stockAmount, currUnitPrice )

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
            date = tupleValue[2]
            if date is None:
                return datetime.min
            return date

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

    ## 0 - first version
    ## 1 - dict instead of list
    ## 2 - sort transactions
    _class_version = 2

    def __init__(self):
        ## ticker, amount, unit price
        self.stockList: Dict[ str, self.History ] = dict()

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

    def size(self):
        return len( self.stockList )

    def clear(self):
        self.stockList.clear()

    def transactions(self, ticker) -> 'History':
        return self.stockList.get( ticker, None )

    def items(self) -> List[ Tuple[str, int, float] ]:
        ret = list()
        for key, hist in self.stockList.items():
            if key is None:
                _LOGGER.warning("found wallet None key")
                continue
            val = hist.calc2()
            if val is not None:
                ret.append( (key, val[0], val[1]) )
        return ret

    def add( self, ticker, amount, unitPrice, transTime: datetime=datetime.today(), joinSimilar=True ):
        transactions = self.stockList.get( ticker, None )
        if transactions is None:
            transactions = self.History()
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
    _class_version = 1

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


class GpwIntradayMap():

    def __init__(self):
        self.dataDict = dict()
    
    def getData(self, isin):
        source = self.getSource(isin)
        return source.getWorksheet()
    
    def getSource(self, isin):
        source = self.dataDict.get( isin, None )
        if source is not None:
            return source
        source = GpwCurrentIntradayData( isin )
        self.dataDict[ isin ] = source
        return source
    
    def refreshData(self, forceRefresh=True):
        for val in self.dataDict.values():
            val.refreshData( forceRefresh )


## =========================================================================


def instance_download_data(obj):
    """Wrapper/alias for object.

    Alias for instance method that allows the method to be called in a
    multiprocessing pool
    """
    obj.downloadData()
    return


def heavy_comp( limit ):
    _LOGGER.info( "computing: %s", limit )
    fact = 1
    for i in range( 1, limit + 1 ):
        fact = fact * i
    return fact


class DataObject( QObject ):

    favsAdded           = pyqtSignal( str )        ## emit group
    favsRemoved         = pyqtSignal( str )        ## emit group
    favsReordered       = pyqtSignal()
    favsRenamed         = pyqtSignal( str, str )   ## from, to
    favsChanged         = pyqtSignal()

    stockDataChanged    = pyqtSignal()
    stockHeadersChanged = pyqtSignal()
    walletDataChanged   = pyqtSignal()

    def __init__(self, parent: QWidget=None):
        super().__init__( parent )
        self.parentWidget = parent

        self.userContainer      = UserContainer()                   ## user data
        
        self.gpwCurrentSource   = StockData( GpwCurrentData() )
        self.gpwIntradayData    = GpwIntradayMap()
        
        self.gpwIndexesData     = GpwIndexesData()
        self.globalIndexesData  = GlobalIndexesData()
        self.gpwIndicatorsData  = GpwIndicatorsData()
        self.gpwDividendsData   = DividendsCalendarData()

        self.gpwReportsData     = FinRepsCalendarData()
        self.gpwPubReportsData  = PublishedFinRepsCalendarData()

        self.gpwIsinMap         = GpwIsinMapData()

        self.undoStack = QUndoStack(self)

    def store( self, outputDir ):
        outputFile = outputDir + "/gpwcurrentheaders.obj"
        persist.store_object( self.gpwCurrentHeaders, outputFile )
        return self.userContainer.store( outputDir )

    def load( self, inputDir ):
        self.userContainer.load( inputDir )
        inputFile = inputDir + "/gpwcurrentheaders.obj"
        headers = persist.load_object_simple( inputFile, dict() )
        self.gpwCurrentSource.stockHeaders = headers
        #self.gpwCurrentHeaders = headers

    @property
    def favs(self) -> FavData:
        return self.userContainer.favs

    @favs.setter
    def favs(self, newData: FavData):
        self.userContainer.favs = newData

    @property
    def notes(self) -> Dict[str, str]:
        return self.userContainer.notes

    @notes.setter
    def notes(self, newData: Dict[str, str]):
        self.userContainer.notes = newData

    @property
    def wallet(self) -> WalletData:
        return self.userContainer.wallet

    ## ======================================================================

    def addFavGroup(self, name):
        if self.favs.containsGroup( name ):
            return
        self.undoStack.push( AddFavGroupCommand( self, name ) )

    def renameFavGroup(self, fromName, toName):
        self.undoStack.push( RenameFavGroupCommand( self, fromName, toName ) )

    def deleteFavGroup(self, name):
        self.undoStack.push( DeleteFavGroupCommand( self, name ) )

    def addFav(self, group, favItem):
        favsSet = self.favs.getFavs( group )
        if favsSet is None:
            favsSet = set()
        favsSet = set( favsSet )
        itemsSet = set( favItem )
        diffSet = itemsSet - favsSet
        if len(diffSet) < 1:
            #_LOGGER.warning( "nothing to add: %s input: %s", diffSet, favItem )
            return
        self.undoStack.push( AddFavCommand( self, group, diffSet ) )

    def deleteFav(self, group, favItem):
        itemsSet = set( favItem )
        self.undoStack.push( DeleteFavCommand( self, group, itemsSet ) )

    def reorderFavGroups(self, newOrder):
        self.undoStack.push( ReorderFavGroupsCommand( self, newOrder ) )

    def getFavStock(self, favGroup):
        stockList = self.favs.getFavs( favGroup )
        return self.gpwCurrentData.getStockData( stockList )

    def getWalletStock(self):
        columnsList = ["Nazwa", "Ticker", "Liczba", "Kurs", "Średni kurs nabycia",
                       "Zysk %", "Zysk", "Wartość", "Zysk całkowity"]

        currentStock: GpwCurrentData = self.gpwCurrentSource.stockData
        currUnitValueIndex = currentStock.getColumnIndex( CurrentDataType.RECENT_TRANS )
        rowsList = []

        for ticker, transactions in self.wallet.stockList.items():
            amount, buy_unit_price = transactions.calc2()
            tickerRow = currentStock.getRowByTicker( ticker )

            if tickerRow.empty:
                _LOGGER.warning( "could not find stock by ticker: %s", ticker )
                rowsList.append( ["-", ticker, amount, "-", buy_unit_price, "-", "-", "-", "-"] )
                continue

            stockName = tickerRow["Nazwa"]

            if amount == 0:
                totalProfit = transactions.transactionsProfit()
                totalProfit = round( totalProfit, 2 )
                rowsList.append( [stockName, ticker, amount, "-", "-", "-", "-", "-", totalProfit] )
                continue

            currUnitValueRaw = tickerRow.iloc[currUnitValueIndex]
            currUnitValue    = 0
            if currUnitValueRaw != "-":
                currUnitValue = float( currUnitValueRaw )

            currValue = currUnitValue * amount
            buyValue  = buy_unit_price * amount
            profit    = currValue - buyValue
            profitPnt = 0
            if buyValue != 0:
                profitPnt = profit / buyValue * 100.0

            totalProfit  = transactions.transactionsProfit()
            totalProfit += currValue - broker_commission( currValue )

            buy_unit_price = round( buy_unit_price, 4 )
            profitPnt      = round( profitPnt, 2 )
            profit         = round( profit, 2 )
            currValue      = round( currValue, 2 )
            totalProfit    = round( totalProfit, 2 )

            rowsList.append( [stockName, ticker, amount, currUnitValue, buy_unit_price,
                              profitPnt, profit, currValue, totalProfit] )

        dataFrame = DataFrame.from_records( rowsList, columns=columnsList )
        return dataFrame

    def getWalletProfit(self):
        currentStock: GpwCurrentData = self.gpwCurrentSource.stockData
        currUnitValueIndex = currentStock.getColumnIndex( CurrentDataType.RECENT_TRANS )

        walletProfit  = 0
        overallProfit = 0
        for ticker, transactions in self.wallet.stockList.items():
            amount, buy_unit_price = transactions.calc2()

            if amount == 0:
                totalProfit    = transactions.transactionsProfit()
                overallProfit += totalProfit
                continue

            tickerRow = currentStock.getRowByTicker( ticker )
            if tickerRow.empty:
                _LOGGER.warning( "could not find stock by ticker: %s", ticker )
                continue

            currUnitValueRaw = tickerRow.iloc[currUnitValueIndex]
            currUnitValue    = 0
            if currUnitValueRaw != "-":
                currUnitValue = float( currUnitValueRaw )

            currValue = currUnitValue * amount
            currCommission = broker_commission( currValue )
            buyValue  = buy_unit_price * amount
            profit    = currValue - buyValue
            profit   -= currCommission

            walletProfit  += profit

            totalProfit    = transactions.transactionsProfit()
            totalProfit   += currValue - currCommission
            overallProfit += totalProfit

        walletProfit  = round( walletProfit, 2 )
        overallProfit = round( overallProfit, 2 )
        return ( walletProfit, overallProfit )

    # pylint: disable=R0914
    def getWalletTransactions(self):
        columnsList = [ "Nazwa", "Ticker", "Liczba", "Kurs", "Kurs nabycia",
                        "Zysk %", "Zysk", "Data nabycia" ]

        currentStock: GpwCurrentData = self.gpwCurrentSource.stockData
        currUnitValueIndex = currentStock.getColumnIndex( CurrentDataType.RECENT_TRANS )
        rowsList = []

        for ticker, transactions in self.wallet.stockList.items():
            tickerRow = currentStock.getRowByTicker( ticker )
            if tickerRow.empty:
                _LOGGER.warning( "could not find stock by ticker: %s", ticker )
                currTransactions = transactions.currentTransactions()
                for item in currTransactions:
                    amount         = item[0]
                    buy_unit_price = item[1]
                    buy_date       = item[2]
                    rowsList.append( ["-", ticker, amount, "-", buy_unit_price, "-", "-", buy_date] )
                continue

            currUnitValue    = 0
            currUnitValueRaw = tickerRow.iloc[currUnitValueIndex]
            if currUnitValueRaw != "-":
                currUnitValue = float( currUnitValueRaw )

            currTransactions = transactions.currentTransactions()
            for item in currTransactions:
                stockName = tickerRow["Nazwa"]

                amount         = item[0]
                buy_unit_price = item[1]
                buy_date       = item[2]

                currValue = currUnitValue * amount
                buyValue  = buy_unit_price * amount
                profit    = currValue - buyValue
                profitPnt = 0
                if buyValue != 0:
                    profitPnt = profit / buyValue * 100.0

                buy_unit_price = round( buy_unit_price, 4 )
                profitPnt      = round( profitPnt, 2 )
                profit         = round( profit, 2 )

                rowsList.append( [ stockName, ticker, amount, currUnitValue, buy_unit_price,
                                   profitPnt, profit, buy_date ] )

        dataFrame = DataFrame.from_records( rowsList, columns=columnsList )
        return dataFrame

    def importWalletTransactions(self, dataFrame: DataFrame, addTransactions=False):
        wallet: WalletData = self.wallet

        if addTransactions is False:
            wallet.clear()

        for _, row in dataFrame.iterrows():
            transTime  = row['trans_time']
            stockName  = row['name']
            oper       = row['k_s']
            amount     = row['amount']
            unit_price = row['unit_price']

#             print("raw row:", transTime, stockName, oper, amount, unit_price)

            dateObject = None
            try:
                ## 31.03.2020 13:21:44
                dateObject = datetime.strptime(transTime, '%d.%m.%Y %H:%M:%S')
            except ValueError:
                dateObject = None

            ticker = self.getTickerFromName( stockName )
            if ticker is None:
                _LOGGER.warning( "could not find stock ticker for name: >%s<", stockName )
                continue

            if oper == "K":
                wallet.add( ticker,  amount, unit_price, dateObject )
            elif oper == "S":
                wallet.add( ticker, -amount, unit_price, dateObject )

        self.walletDataChanged.emit()

    ## ======================================================================

    def loadDownloadedStocks(self):
        stockList = self.stockRefreshList()
        for func, args in stockList:
            func( *args )

    def refreshStockData(self, forceRefresh=True):
#         threads = threadlist.QThreadList( self )
#         threads = threadlist.SerialList( self )
        threads = threadlist.QThreadMeasuredList( self )
#         threads = threadlist.ProcessList( self )

        threads.finished.connect( threads.deleteLater )
        threads.finished.connect( self.stockDataChanged, Qt.QueuedConnection )

#         threads.appendFunction( QtCore.QThread.msleep, args=[30*1000] )
#         threads.appendFunction( heavy_comp, [300000] )

        stockList = self.stockRefreshList( forceRefresh )
        for func, args in stockList:
            threads.appendFunction( func, args )

        threads.start()

    def stockRefreshList(self, forceRefresh=False):
        stockList = self.stockProviderList()
        retList = []
        for stock in stockList:
            retList.append( (stock.refreshData, [forceRefresh] ) )
        return retList

#     def stockDownloadList(self):
#         stockList = self.stockProviderList()
#         retList = []
#         for stock in stockList:
#             retList.append( stock.downloadData )
#         return retList

    def stockProviderList(self):
        retList = []
        retList.append( self.gpwCurrentSource )
        retList.append( self.gpwIntradayData )
        retList.append( self.gpwIndexesData )
        retList.append( self.globalIndexesData )
        retList.append( self.gpwIndicatorsData )
        retList.append( self.gpwDividendsData )
        retList.append( self.gpwReportsData )
        retList.append( self.gpwPubReportsData )
        retList.append( self.gpwIsinMap )
        return retList

    @property
    def gpwCurrentData(self):
        return self.gpwCurrentSource.stockData

    @property
    def gpwCurrentHeaders(self) -> Dict[ int, str ]:
        return self.gpwCurrentSource.stockHeaders

    @gpwCurrentHeaders.setter
    def gpwCurrentHeaders(self, headersDict):
        self.gpwCurrentSource.stockHeaders = headersDict
        self.stockHeadersChanged.emit()

    def getIntradayData(self, ticker):
        isin = self.getStockIsinFromTicker(ticker)
        return self.gpwIntradayData.getData(isin)
    
    def getTicker(self, rowIndex):
        return self.gpwCurrentSource.stockData.getTickerField( rowIndex )

    def getTickerFromIsin(self, stockIsin):
        return self.gpwIsinMap.getTickerFromIsin( stockIsin )

    def getTickerFromName(self, stockName):
        return self.gpwIsinMap.getTickerFromName( stockName )

    def getStockIsinFromTicker(self, ticker):
        return self.gpwIsinMap.getStockIsinFromTicker( ticker )

    def getNameFromTicker(self, ticker):
        return self.gpwIsinMap.getNameFromTicker( ticker )


def broker_commission( value ):
    ## always returns positive value
    commission = 0.0
    if value > 0.0:
        commission = value * 0.0039
        commission = max( commission,  3.0 )
    else:
        commission = value * 0.0039
        commission = -min( commission, -3.0 )
    return commission
