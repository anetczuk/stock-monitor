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
from typing import Dict
# from multiprocessing import Process, Queue
# from multiprocessing import Pool

from datetime import datetime

from pandas.core.frame import DataFrame

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QUndoStack

from stockmonitor import persist
from stockmonitor.dataaccess.datatype import CurrentDataType
# from stockmonitor.dataaccess.gpw.gpwdata import GpwIsinMapData
from stockmonitor.dataaccess.gpw.gpwdata import GpwIndicatorsData
from stockmonitor.dataaccess.dividendsdata import DividendsCalendarData
from stockmonitor.dataaccess.finreportscalendardata import PublishedFinRepsCalendarData, FinRepsCalendarData
from stockmonitor.dataaccess.globalindexesdata import GlobalIndexesData
from stockmonitor.dataaccess.gpw.gpwcurrentdata import GpwCurrentStockData,\
    GpwCurrentIndexesData

import stockmonitor.gui.threadlist as threadlist
from stockmonitor.gui.command.addfavgroupcommand import AddFavGroupCommand
from stockmonitor.gui.command.deletefavgroupcommand import DeleteFavGroupCommand
from stockmonitor.gui.command.renamefavgroupcommand import RenameFavGroupCommand
from stockmonitor.gui.command.addfavcommand import AddFavCommand
from stockmonitor.gui.command.deletefavcommand import DeleteFavCommand
from stockmonitor.gui.command.reorderfavgroupscommand import ReorderFavGroupsCommand
from stockmonitor.gui.datatypes import UserContainer, StockData,\
    GpwStockIntradayMap, GpwIndexIntradayMap, FavData, WalletData,\
    broker_commission, TransHistory


_LOGGER = logging.getLogger(__name__)


READONLY_FAV_GROUPS = ["All", "Wallet"]


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

    favsGrpChanged      = pyqtSignal( str )        ## emit group
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

        self.gpwCurrentSource     = StockData( GpwCurrentStockData() )
        self.gpwStockIntradayData = GpwStockIntradayMap()
        self.gpwIndexIntradayData = GpwIndexIntradayMap()

        self.gpwIndexesData     = GpwCurrentIndexesData()
        self.globalIndexesData  = GlobalIndexesData()
        self.gpwIndicatorsData  = GpwIndicatorsData()
        self.gpwDividendsData   = DividendsCalendarData()

        self.gpwReportsData     = FinRepsCalendarData()
        self.gpwPubReportsData  = PublishedFinRepsCalendarData()

#         self.gpwIsinMap         = GpwIsinMapData()

        self.undoStack = QUndoStack(self)

        self.favsGrpChanged.connect( self.updateAllFavsGroup )
        self.favsChanged.connect( self.updateAllFavsGroup )

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
        self.updateWalletFavGroup()
        self.updateAllFavsGroup()

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
        currFavsSet = self.favs.getFavs( group )
        if currFavsSet is None:
            currFavsSet = set()
        currFavsSet = set( currFavsSet )
        newItemsSet = set( favItem )
        diffSet = newItemsSet - currFavsSet
        if len(diffSet) < 1:
            #_LOGGER.warning( "nothing to add: %s input: %s", diffSet, favItem )
            return
        self.undoStack.push( AddFavCommand( self, group, diffSet ) )

    def deleteFav(self, group, favItem):
        itemsSet = set( favItem )
        self.undoStack.push( DeleteFavCommand( self, group, itemsSet ) )

    def reorderFavGroups(self, newOrder):
        self.undoStack.push( ReorderFavGroupsCommand( self, newOrder ) )

    def getAllFavs(self):
        allFavsSet = set()
        for group, favs in self.favs.favsList.items():
            if group == "All":
                continue
            allFavsSet |= set( favs )
        return allFavsSet

    def getFavStock(self, favGroup):
        stockList = self.favs.getFavs( favGroup )
        return self.gpwCurrentData.getStockData( stockList )

    def getWalletStock(self):
        columnsList = [ "Nazwa", "Ticker", "Liczba", "Kurs", "Zm.do k.odn.(%)",
                        "Średni kurs nabycia", "Zysk %", "Zysk", "Wartość", "Zysk całkowity" ]
        # apply_on_column( dataFrame, 'Zm.do k.odn.(%)', convert_float )

        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData
        currUnitValueIndex = currentStock.getColumnIndex( CurrentDataType.RECENT_TRANS )
        rowsList = []

        for ticker, transactions in self.wallet.stockList.items():
            amount, buy_unit_price = transactions.currentTransactionsAvg()
            currentStockRow = currentStock.getRowByTicker( ticker )

            if currentStockRow.empty:
                _LOGGER.warning( "could not find stock by ticker: %s", ticker )
                rowsList.append( ["-", ticker, amount, "-", buy_unit_price, "-", "-", "-", "-"] )
                continue

            stockName = currentStockRow["Nazwa"]

            if amount == 0:
                totalProfit = transactions.transactionsProfit()
                totalProfit = round( totalProfit, 2 )
                rowsList.append( [stockName, ticker, amount, "-", "-", "-", "-", "-", totalProfit] )
                continue

            currUnitValueRaw = currentStockRow.iloc[ currUnitValueIndex ]
            currUnitValue    = 0
            if currUnitValueRaw != "-":
                currUnitValue = float( currUnitValueRaw )

            currChangeRaw = currentStockRow.iloc[ 12 ]
            currChange    = 0
            if currChangeRaw != "-":
                currChange = float( currChangeRaw )

            currValue = currUnitValue * amount
            buyValue  = buy_unit_price * amount
            profit    = currValue - buyValue
            profitPnt = 0
            if buyValue != 0:
                profitPnt = profit / buyValue * 100.0

            totalProfit  = transactions.transactionsProfit()
            totalProfit += currValue - broker_commission( currValue )

            buy_unit_price = round( buy_unit_price, 4 )
            currChange     = round( currChange, 2 )
            profitPnt      = round( profitPnt, 2 )
            profit         = round( profit, 2 )
            currValue      = round( currValue, 2 )
            totalProfit    = round( totalProfit, 2 )

            rowsList.append( [ stockName, ticker, amount, currUnitValue, currChange,
                               buy_unit_price, profitPnt, profit, currValue, totalProfit ] )

        dataFrame = DataFrame.from_records( rowsList, columns=columnsList )
        return dataFrame

    def getWalletState(self):
        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData
        currUnitValueIndex = currentStock.getColumnIndex( CurrentDataType.RECENT_TRANS )

        walletValue   = 0.0
        walletProfit  = 0.0
        overallProfit = 0.0
        for ticker, transactions in self.wallet.stockList.items():
            amount, buy_unit_price = transactions.currentTransactionsAvg()

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

            walletValue  += currValue
            walletProfit += profit

            totalProfit    = transactions.transactionsProfit()
            totalProfit   += currValue - currCommission
            overallProfit += totalProfit

        walletValue   = round( walletValue, 2 )
        walletProfit  = round( walletProfit, 2 )
        overallProfit = round( overallProfit, 2 )
        return ( walletValue, walletProfit, overallProfit )

    # pylint: disable=R0914
    def getWalletTransactions(self):
        columnsList = [ "Nazwa", "Ticker", "Liczba", "Kurs transakcji",
                        "Kurs", "Zm.do k.odn.(%)",
                        "Zysk %", "Zysk", "Data transakcji" ]

        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData
        currUnitValueIndex = currentStock.getColumnIndex( CurrentDataType.RECENT_TRANS )
        rowsList = []

        ticker: str
        transactions: TransHistory
        for ticker, transactions in self.wallet.stockList.items():
#             if ticker == "PCX":
#                 print( "xxxxx:\n", transactions.items() )
            currentStockRow = currentStock.getRowByTicker( ticker )
            if currentStockRow.empty:
                _LOGGER.warning( "could not find stock by ticker: %s", ticker )
                currTransactions = transactions.currentTransactions()
                for item in currTransactions:
                    trans_amount     = item[0]
                    trans_unit_price = item[1]
                    trans_date       = item[2]
                    rowsList.append( ["-", ticker, trans_amount, trans_unit_price, "-", "-", "-", "-", trans_date] )
                continue

            currUnitValue    = 0
            currUnitValueRaw = currentStockRow.iloc[currUnitValueIndex]
            if currUnitValueRaw != "-":
                currUnitValue = float( currUnitValueRaw )

            currChangeRaw = currentStockRow.iloc[ 12 ]
            currChange    = 0
            if currChangeRaw != "-":
                currChange = float( currChangeRaw )

            currTransactions = transactions.currentTransactions()
            for item in currTransactions:
                stockName = currentStockRow["Nazwa"]

                trans_amount     = item[0]
                trans_unit_price = item[1]
                trans_date       = item[2]

                currValue = currUnitValue * trans_amount
                buyValue  = trans_unit_price * trans_amount
                profit    = currValue - buyValue
                profitPnt = 0
                if buyValue != 0:
                    profitPnt = profit / buyValue * 100.0

                trans_unit_price = round( trans_unit_price, 4 )
                profitPnt      = round( profitPnt, 2 )
                profit         = round( profit, 2 )

                rowsList.append( [ stockName, ticker, trans_amount, trans_unit_price,
                                   currUnitValue, currChange,
                                   profitPnt, profit, trans_date ] )

        dataFrame = DataFrame.from_records( rowsList, columns=columnsList )
        return dataFrame

    # pylint: disable=R0914
    def getAllTransactions(self):
        columnsList = [ "Nazwa", "Ticker", "Liczba", "Kurs transakcji",
                        "Kurs", "Zm.do k.odn.(%)",
                        "Zysk %", "Zysk", "Data transakcji" ]

        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData
        currUnitValueIndex = currentStock.getColumnIndex( CurrentDataType.RECENT_TRANS )
        rowsList = []

        for ticker, transactions in self.wallet.stockList.items():
            currentStockRow = currentStock.getRowByTicker( ticker )
            if currentStockRow.empty:
                _LOGGER.warning( "could not find stock by ticker: %s", ticker )
                currTransactions = transactions.allTransactions()
                for item in currTransactions:
                    trans_amount     = item[0]
                    trans_unit_price = item[1]
                    trans_date       = item[2]
                    rowsList.append( ["-", ticker, trans_amount, trans_unit_price, "-", "-", "-", "-", trans_date] )
                continue

            currAmount = transactions.currentAmount()

            currUnitValue    = 0
            currUnitValueRaw = currentStockRow.iloc[currUnitValueIndex]
            if currUnitValueRaw != "-":
                currUnitValue = float( currUnitValueRaw )

            currChangeRaw = currentStockRow.iloc[ 12 ]
            currChange    = 0
            if currChangeRaw != "-":
                currChange = float( currChangeRaw )

            currTransactions = transactions.allTransactions()
            for item in currTransactions:
                stockName = currentStockRow["Nazwa"]

                trans_amount     = item[0]
                trans_unit_price = item[1]
                trans_date       = item[2]

                if currAmount <= 0:
                    trans_unit_price = round( trans_unit_price, 4 )
                    profitPnt        = "-"
                    profit           = "-"
                else:
                    currValue = abs( currUnitValue * trans_amount )
                    buyValue  = abs( trans_unit_price * trans_amount )

                    profit    = currValue - buyValue
                    profitPnt = 0
                    if buyValue != 0:
                        profitPnt = profit / buyValue * 100.0

                    trans_unit_price = round( trans_unit_price, 4 )
                    profitPnt        = round( profitPnt, 2 )
                    profit           = round( profit, 2 )

                rowsList.append( [ stockName, ticker, trans_amount, trans_unit_price,
                                   currUnitValue, currChange,
                                   profitPnt, profit, trans_date ] )

        dataFrame = DataFrame.from_records( rowsList, columns=columnsList )
        return dataFrame

    def getWalletStockValueData(self, ticker, rangeCode):
        transactions: TransHistory = self.wallet.transactions( ticker )
        if transactions is None:
            return None

        isin = self.getStockIsinFromTicker( ticker )
        intraSource = self.gpwStockIntradayData.getSource( isin, rangeCode )
        stockData = intraSource.getWorksheet()

        startDateTime = stockData.iloc[0, 0]        ## first date
        startDate = startDateTime.date()

        transList = list()
        for item in transactions:
            transTime = item[2]
            transDate = transTime.date()
            if transDate < startDate:
                continue
            transList.append( item )

        amountBefore = transactions.amountBeforeDate( startDate )
        dataFrame = stockData[ ["t", "c"] ].copy()

        if len( transList ) < 1:
            dataFrame[ "c" ] = dataFrame[ "c" ] * amountBefore
            return dataFrame

        rowsNum = dataFrame.shape[0]

        rowIndex   = 0
        currAmount = amountBefore

        for item in reversed( transList ):
            transTime = item[2]
            while rowIndex < rowsNum:
                if dataFrame.at[ rowIndex, "t" ] < transTime:
                    dataFrame.at[ rowIndex, "c" ] = dataFrame.at[ rowIndex, "c" ] * currAmount
                    rowIndex += 1
                else:
                    break
            currAmount += item[0]

        while rowIndex < rowsNum:
            dataFrame.at[ rowIndex, "c" ] = dataFrame.at[ rowIndex, "c" ] * currAmount
            rowIndex += 1

        return dataFrame

#     def getWalletStockProfitData(self, ticker, rangeCode):
#         transactions: TransHistory = self.wallet.transactions( ticker )
#         if transactions is None:
#             return None
#
#         isin = self.getStockIsinFromTicker( ticker )
#         intraSource = self.gpwStockIntradayData.getSource( isin, rangeCode )
#         stockData = intraSource.getWorksheet()
#
#         startDateTime = stockData.iloc[0, 0]        ## first date
#         startDate = startDateTime.date()
#
#         transList = list()
#         for item in transactions:
#             transTime = item[2]
#             transDate = transTime.date()
#             if transDate < startDate:
#                 continue
#             transList.append( item )
#
#         amountBefore = transactions.amountBeforeDate( startDate )
#         dataFrame = stockData[ ["t", "c"] ].copy()
#
#         if len( transList ) < 1:
#             dataFrame[ "c" ] = dataFrame[ "c" ] * amountBefore
#             return dataFrame
#
#         rowsNum = dataFrame.shape[0]
#
#         rowIndex   = 0
#         currAmount = amountBefore
#
#         for item in reversed( transList ):
#             transTime = item[2]
#             while rowIndex < rowsNum:
#                 if dataFrame.at[ rowIndex, "t" ] < transTime:
#                     dataFrame.at[ rowIndex, "c" ] = dataFrame.at[ rowIndex, "c" ] * currAmount
#                     rowIndex += 1
#                 else:
#                     break
#             currAmount += item[0]
#
#         while rowIndex < rowsNum:
#             dataFrame.at[ rowIndex, "c" ] = dataFrame.at[ rowIndex, "c" ] * currAmount
#             rowIndex += 1
#
#         return dataFrame

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

        self.updateWalletFavGroup()

    def updateWalletFavGroup(self):
        wallet: WalletData = self.wallet
        walletSet = set( wallet.getCurrentStock() )

        currFavsSet = self.favs.getFavs( "Wallet" )
        if currFavsSet is None:
            currFavsSet = set()
        else:
            currFavsSet = set( currFavsSet )

        if walletSet != currFavsSet:
            _LOGGER.debug("updating Wallet favs")
            self.favs.setFavs( "Wallet", walletSet )
            self.favsGrpChanged.emit( "Wallet" )

    def updateAllFavsGroup(self):
        allFavsSet = self.getAllFavs()

        currFavsSet = self.favs.getFavs( "All" )
        if currFavsSet is None:
            currFavsSet = set()
        else:
            currFavsSet = set( currFavsSet )

        if allFavsSet != currFavsSet:
            _LOGGER.debug("updating All favs")
            self.favs.setFavs( "All", allFavsSet )
            self.favsGrpChanged.emit( "All" )

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
        retList.append( self.gpwStockIntradayData )
        retList.append( self.gpwIndexIntradayData )
        retList.append( self.gpwIndexesData )
        retList.append( self.globalIndexesData )
        retList.append( self.gpwIndicatorsData )
        retList.append( self.gpwDividendsData )
        retList.append( self.gpwReportsData )
        retList.append( self.gpwPubReportsData )
#         retList.append( self.gpwIsinMap )
        return retList

    @property
    def gpwCurrentData(self) -> GpwCurrentStockData:
        return self.gpwCurrentSource.stockData                  # type: ignore

    @property
    def gpwCurrentHeaders(self) -> Dict[ int, str ]:
        return self.gpwCurrentSource.stockHeaders

    @gpwCurrentHeaders.setter
    def gpwCurrentHeaders(self, headersDict):
        self.gpwCurrentSource.stockHeaders = headersDict
        self.stockHeadersChanged.emit()

    def getStockIntradayDataByTicker(self, ticker):
        isin = self.getStockIsinFromTicker(ticker)
        return self.gpwStockIntradayData.getData(isin)

    def getStockIntradayDataByIsin(self, isin):
        return self.gpwStockIntradayData.getData(isin)

    def getIndexIntradayDataByIsin(self, isin):
        return self.gpwIndexIntradayData.getData(isin)

    def getTicker(self, rowIndex):
        return self.gpwCurrentSource.stockData.getTickerField( rowIndex )

    def getTickerFromIsin(self, stockIsin):
        return self.gpwCurrentData.getTickerFromIsin( stockIsin )

    def getTickerFromName(self, stockName):
        return self.gpwCurrentData.getTickerFromName( stockName )

    def getStockIsinFromTicker(self, ticker):
        return self.gpwCurrentData.getStockIsinFromTicker( ticker )

    def getNameFromTicker(self, ticker):
        return self.gpwCurrentData.getNameFromTicker( ticker )
