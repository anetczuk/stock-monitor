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

from pandas.core.frame import DataFrame

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QUndoStack

from stockdataaccess.dataaccess.gpw.gpwcurrentdata import GpwCurrentStockData, \
    GpwCurrentIndexesData
from stockdataaccess.dataaccess.gpw.gpwdata import GpwIndicatorsData
from stockdataaccess.dataaccess.gpw.gpwespidata import GpwESPIData
from stockdataaccess.dataaccess.finreportscalendardata import FinRepsCalendarData, PublishedFinRepsCalendarData
from stockdataaccess.dataaccess.dividendsdata import DividendsCalendarData
from stockdataaccess.dataaccess.globalindexesdata import GlobalIndexesData
from stockdataaccess.dataaccess.shortsellingsdata import CurrentShortSellingsData, \
    HistoryShortSellingsData

from stockmonitor.datatypes.datatypes import FavData, WalletData, \
    TransactionMatchMode, MarkersContainer, \
    MarkerEntry
from stockmonitor.datatypes.datacontainer import DataContainer
from stockmonitor.datatypes.stocktypes import BaseWorksheetDAOProvider, GpwStockIntradayMap, \
    GpwIndexIntradayMap

from stockmonitor.gui import threadlist
from stockmonitor.gui.command.addfavgroupcommand import AddFavGroupCommand
from stockmonitor.gui.command.deletefavgroupcommand import DeleteFavGroupCommand
from stockmonitor.gui.command.renamefavgroupcommand import RenameFavGroupCommand
from stockmonitor.gui.command.addfavcommand import AddFavCommand
from stockmonitor.gui.command.deletefavcommand import DeleteFavCommand
from stockmonitor.gui.command.reorderfavgroupscommand import ReorderFavGroupsCommand
from stockmonitor.gui.command.addmarkercommand import AddMarkerCommand
from stockmonitor.gui.command.editmarketcommand import EditMarketCommand
from stockmonitor.gui.command.deletemarkercommand import DeleteMarkerCommand


_LOGGER = logging.getLogger(__name__)


READONLY_FAV_GROUPS = ["All", "Wallet", "Markers"]


def heavy_comp( limit ):
    _LOGGER.info( "computing: %s", limit )
    fact = 1
    for i in range( 1, limit + 1 ):
        fact = fact * i
    return fact


def group_by_day( tansactionsList ):
    return tansactionsList


## ============================================================================


##
##
##
class DataObject( QObject ):

    favsGrpChanged      = pyqtSignal( str )        ## emit group
    favsReordered       = pyqtSignal()
    favsRenamed         = pyqtSignal( str, str )   ## from, to
    favsChanged         = pyqtSignal()

    markersChanged      = pyqtSignal()

    stockDataChanged    = pyqtSignal()
    stockHeadersChanged = pyqtSignal()
    walletDataChanged   = pyqtSignal()

    def __init__(self, parent: QWidget = None):
        super().__init__( parent )
        self.parentWidget = parent

        self.dataContainer = DataContainer()

        self.undoStack = QUndoStack(self)

        self.markersChanged.connect( self.updateMarkersFavGroup )

        self.favsGrpChanged.connect( self.updateAllFavsGroup )
        self.favsChanged.connect( self.updateAllFavsGroup )

    def store( self, outputDir ):
        return self.dataContainer.store( outputDir )

    def load( self, inputDir ):
        return self.dataContainer.load( inputDir )

    ## ======================================================================

    @property
    def wallet(self) -> WalletData:
        return self.dataContainer.wallet

    @property
    def favs(self) -> FavData:
        return self.dataContainer.favs

    @favs.setter
    def favs(self, newData: FavData):
        self.dataContainer.favs = newData

    @property
    def markers(self) -> MarkersContainer:
        return self.dataContainer.markers

    @markers.setter
    def markers(self, newData: MarkersContainer):
        self.dataContainer.markers = newData

    @property
    def notes(self) -> Dict[str, str]:
        return self.dataContainer.notes

    @notes.setter
    def notes(self, newData: Dict[str, str]):
        self.dataContainer.notes = newData

    ## ======================================================================

    @property
    def gpwCurrentHeaders(self) -> Dict[ int, str ]:
        return self.dataContainer.gpwCurrentSource.stockHeaders

    @gpwCurrentHeaders.setter
    def gpwCurrentHeaders(self, headersDict):
        self.dataContainer.gpwCurrentSource.stockHeaders = headersDict
        self.stockHeadersChanged.emit()

    @property
    def gpwCurrentSource(self) -> BaseWorksheetDAOProvider:
        return self.dataContainer.gpwCurrentSource

    @property
    def gpwCurrentData(self) -> GpwCurrentStockData:
        return self.dataContainer.gpwCurrentData

    @property
    def gpwStockIntradayData(self) -> GpwStockIntradayMap:
        return self.dataContainer.gpwStockIntradayData

    @property
    def gpwIndexIntradayData(self) -> GpwIndexIntradayMap:
        return self.dataContainer.gpwIndexIntradayData

    @property
    def gpwESPIData(self) -> GpwESPIData:
        return self.dataContainer.gpwESPIData

    @property
    def gpwIndexesData(self) -> GpwCurrentIndexesData:
        return self.dataContainer.gpwIndexesData

    @property
    def globalIndexesData(self) -> GlobalIndexesData:
        return self.dataContainer.globalIndexesData

    @property
    def gpwIndicatorsData(self) -> GpwIndicatorsData:
        return self.dataContainer.gpwIndicatorsData

    @property
    def gpwDividendsData(self) -> DividendsCalendarData:
        return self.dataContainer.gpwDividendsData

    @property
    def gpwReportsData(self) -> FinRepsCalendarData:
        return self.dataContainer.gpwReportsData

    @property
    def gpwPubReportsData(self) -> PublishedFinRepsCalendarData:
        return self.dataContainer.gpwPubReportsData

    @property
    def gpwCurrentShortSellingsData(self) -> CurrentShortSellingsData:
        return self.dataContainer.gpwCurrentShortSellingsData

    @property
    def gpwHistoryShortSellingsData(self) -> HistoryShortSellingsData:
        return self.dataContainer.gpwHistoryShortSellingsData

    ## ======================================================================

    def getAllFavs(self):
        return self.dataContainer.getAllFavs()

    def getFavStock(self, favGroup):
        return self.dataContainer.getFavStock( favGroup )

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

    ## ======================================================================

    def getMarkersData(self):
        return self.dataContainer.getMarkersData()

    def addMarkersList(self, tickersList, operation):
        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData
        markersList = []
        for ticker in tickersList:
            currValue = currentStock.getRecentValueByTicker( ticker )
            newMarker = MarkerEntry()
            newMarker.ticker = ticker
            newMarker.value = currValue
            newMarker.setOperation( operation )
            markersList.append( newMarker )
        self.undoStack.push( AddMarkerCommand( self, markersList ) )

    def addMarkerEntry(self, entry):
        markersList = []
        markersList.append( entry )
        self.undoStack.push( AddMarkerCommand( self, markersList ) )

    def replaceMarkerEntry(self, oldEntry, newEntry):
        self.undoStack.push( EditMarketCommand( self, oldEntry, newEntry ) )

    def removeMarkerEntry(self, entry):
        self.undoStack.push( DeleteMarkerCommand( self, entry ) )

    ## ======================================================================

    def transactionsMatchMode(self):
        return self.dataContainer.transactionsMatchMode()

    def matchTransactionsOldest(self):
        self.dataContainer.userContainer.transactionsMatchMode = TransactionMatchMode.OLDEST
        self.walletDataChanged.emit()

    def matchTransactionsBest(self):
        self.dataContainer.userContainer.transactionsMatchMode = TransactionMatchMode.BEST
        self.walletDataChanged.emit()

    def matchTransactionsRecent(self):
        self.dataContainer.userContainer.transactionsMatchMode = TransactionMatchMode.RECENT_PROFIT
        self.walletDataChanged.emit()

    ## ======================================================================

    def clearWalletTransactions(self):
        self.dataContainer.clearWalletTransactions()

        self.favsGrpChanged.emit( "Wallet" )
        self.walletDataChanged.emit()

    def importWalletTransactions(self, dataFrame: DataFrame, addTransactions=False):
        refreshed = self.dataContainer.importWalletTransactions( dataFrame, addTransactions )
        if refreshed is False:
            return False

        self.favsGrpChanged.emit( "Wallet" )
        self.walletDataChanged.emit()
        return True

    def updateAllFavsGroup(self):
        changed = self.dataContainer.updateAllFavsGroup()
        if changed:
            self.favsGrpChanged.emit( "All" )

    def updateWalletFavGroup(self):
        changed = self.dataContainer.updateWalletFavGroup()
        if changed:
            self.favsGrpChanged.emit( "Wallet" )

    def updateMarkersFavGroup(self):
        changed = self.dataContainer.updateMarkersFavGroup()
        if changed:
            self.favsGrpChanged.emit( "Markers" )

    ## ======================================================================

    def getWalletStock(self):
        return self.dataContainer.getWalletStock()

    def getWalletBuyTransactions(self, groupByDay=False ):
        return self.dataContainer.getWalletBuyTransactions( groupByDay )

    def getWalletSellTransactions(self, groupByDay=False):
        return self.dataContainer.getWalletSellTransactions( groupByDay )

    def getAllTransactions(self, groupByDay=False):
        return self.dataContainer.getAllTransactions( groupByDay )

    def getWalletStockValueData(self, ticker, rangeCode):
        return self.dataContainer.getWalletStockValueData( ticker, rangeCode )

    ## wallet summary: wallet value, wallet profit, ref change, gain, overall profit
    def getWalletState(self, prev_day_ref=True):
        return self.dataContainer.getWalletState(prev_day_ref)

    def getWalletGainHistory(self, rangeCode):
        return self.dataContainer.getWalletGainHistory( rangeCode )

    ## calculate profit of single stock
    def getWalletStockOverallProfitHistory(self, ticker, rangeCode):
        return self.dataContainer.getWalletStockProfitHistory( ticker, rangeCode )

    def getWalletProfitHistory(self, rangeCode, calculateOverall: bool = True):
        return self.dataContainer.getWalletProfitHistory( rangeCode, calculateOverall )

    def getWalletValueHistory(self, rangeCode):
        return self.dataContainer.getWalletValueHistory( rangeCode )

    ## ======================================================================

    def loadDownloadedStocks(self):
        return self.dataContainer.loadDownloadedStocks()

    def refreshStockList(self, forceRefresh=False):
        return self.dataContainer.refreshStockList( forceRefresh )

    def refreshAllList(self, forceRefresh=False):
        return self.dataContainer.refreshAllList( forceRefresh )

    def refreshStockData(self, forceRefresh=True):
        ThreadingListType = threadlist.get_threading_list_class()
        threads = ThreadingListType( self )
        threads.finished.connect( self.stockDataChanged )
        threads.deleteOnFinish()

        stockList = self.refreshStockList( forceRefresh )
        threads.start( stockList )

    def refreshAllData(self, forceRefresh=True):
        ThreadingListType = threadlist.get_threading_list_class()
        threads = ThreadingListType( self )
        threads.finished.connect( self.stockDataChanged )
        threads.deleteOnFinish()

        stockList = self.refreshAllList( forceRefresh )
        threads.start( stockList )

#     def dataAllProvidersList(self) -> List[ StockDataProvider ]:
#         return self.dataContainer.dataAllProvidersList()

#     def dataStockProvidersList(self) -> List[ StockDataProvider ]:
#         return self.dataContainer.dataStockProvidersList()

#     def getStockIntradayDataByTicker(self, ticker):
#         return self.dataContainer.getStockIntradayDataByTicker( ticker )

#     def getStockIntradayDataByIsin(self, isin):
#         return self.dataContainer.getStockIntradayDataByIsin( isin )

#     def getIndexIntradayDataByIsin(self, isin):
#         return self.dataContainer.getIndexIntradayDataByIsin( isin )

    def getTicker(self, rowIndex):
        return self.gpwCurrentData.getTickerField( rowIndex )

    def getTickerFromIsin(self, stockIsin):
        return self.gpwCurrentData.getTickerFromIsin( stockIsin )

    def getTickerFromName(self, stockName):
        return self.gpwCurrentData.getTickerFromName( stockName )

    def getStockIsinFromTicker(self, ticker):
        return self.gpwCurrentData.getStockIsinFromTicker( ticker )

    def getNameFromTicker(self, ticker):
        return self.gpwCurrentData.getNameFromTicker( ticker )

    def getNameFromIsin(self, isin):
        return self.gpwCurrentData.getNameFromIsin( isin )
