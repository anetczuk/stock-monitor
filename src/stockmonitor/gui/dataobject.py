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

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QUndoStack


from stockmonitor.datatypes import TransactionMatchMode, MarkerEntry
from stockmonitor.datacontainer import DataContainer
from stockmonitor.stocktypes import StockData, GpwStockIntradayMap,\
    GpwIndexIntradayMap

import stockmonitor.gui.threadlist as threadlist
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


## ============================================================================


##
##
##
class DataObject( QObject, DataContainer ):

    favsGrpChanged      = pyqtSignal( str )        ## emit group
    favsReordered       = pyqtSignal()
    favsRenamed         = pyqtSignal( str, str )   ## from, to
    favsChanged         = pyqtSignal()

    markersChanged      = pyqtSignal()

    stockDataChanged    = pyqtSignal()
    stockHeadersChanged = pyqtSignal()
    walletDataChanged   = pyqtSignal()

    def __init__(self, parent: QWidget=None):
        super( QObject, self ).__init__( parent )
        self.parentWidget = parent

#         self.dataContainer = DataContainer()
        
        self.undoStack = QUndoStack(self)

        self.markersChanged.connect( self.updateMarkersFavGroup )

        self.favsGrpChanged.connect( self.updateAllFavsGroup )
        self.favsChanged.connect( self.updateAllFavsGroup )

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

    def addMarkersList(self, tickersList, operation):
        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData
        markersList = list()
        for ticker in tickersList:
            currValue = currentStock.getRecentValue( ticker )
            newMarker = MarkerEntry()
            newMarker.ticker = ticker
            newMarker.value = currValue
            newMarker.setOperation( operation )
            markersList.append( newMarker )
        self.undoStack.push( AddMarkerCommand( self, markersList ) )

    def addMarkerEntry(self, entry):
        markersList = list()
        markersList.append( entry )
        self.undoStack.push( AddMarkerCommand( self, markersList ) )

    def replaceMarkerEntry(self, oldEntry, newEntry):
        self.undoStack.push( EditMarketCommand( self, oldEntry, newEntry ) )

    def removeMarkerEntry(self, entry):
        self.undoStack.push( DeleteMarkerCommand( self, entry ) )

    ## ======================================================================

    def matchTransactionsOldest(self):
        self.userContainer.transactionsMatchMode = TransactionMatchMode.OLDEST
        self.walletDataChanged.emit()

    def matchTransactionsBest(self):
        self.userContainer.transactionsMatchMode = TransactionMatchMode.BEST
        self.walletDataChanged.emit()

    def matchTransactionsRecent(self):
        self.userContainer.transactionsMatchMode = TransactionMatchMode.RECENT_PROFIT
        self.walletDataChanged.emit()

    ## ======================================================================

    def importWalletTransactions(self, dataFrame: DataFrame, addTransactions=False):
        super().importWalletTransactions( dataFrame, addTransactions )
        
        self.updateWalletFavGroup()
        self.walletDataChanged.emit()

    def updateAllFavsGroup(self):
        changed = super().updateAllFavsGroup()
        if changed:
            self.favsGrpChanged.emit( "All" )

    def updateWalletFavGroup(self):
        changed = super().updateWalletFavGroup()
        if changed:
            self.favsGrpChanged.emit( "Wallet" )

    def updateMarkersFavGroup(self):
        changed = super().updateMarkersFavGroup()
        if changed:
            self.favsGrpChanged.emit( "Markers" )

    ## ======================================================================

    def refreshStockData(self, forceRefresh=True):
#         threads = threadlist.QThreadList( self )
#         threads = threadlist.SerialList( self )
        threads = threadlist.QThreadMeasuredList( self )
#         threads = threadlist.ProcessList( self )

        threads.finished.connect( threads.deleteLater )
        threads.finished.connect( self.stockDataChanged, Qt.QueuedConnection )

#         threads.appendFunction( QtCore.QThread.msleep, args=[30*1000] )
#         threads.appendFunction( heavy_comp, [300000] )

        stockList = self.refreshStockList( forceRefresh )
        for func, args in stockList:
            threads.appendFunction( func, args )

        threads.start()

    def refreshAllData(self, forceRefresh=True):
#         threads = threadlist.QThreadList( self )
#         threads = threadlist.SerialList( self )
        threads = threadlist.QThreadMeasuredList( self )
#         threads = threadlist.ProcessList( self )

        threads.finished.connect( threads.deleteLater )
        threads.finished.connect( self.stockDataChanged, Qt.QueuedConnection )

#         threads.appendFunction( QtCore.QThread.msleep, args=[30*1000] )
#         threads.appendFunction( heavy_comp, [300000] )

        stockList = self.refreshAllList( forceRefresh )
        for func, args in stockList:
            threads.appendFunction( func, args )

        threads.start()

    @property
    def gpwCurrentHeaders(self) -> Dict[ int, str ]:
        return self.gpwCurrentSource.stockHeaders

    @gpwCurrentHeaders.setter
    def gpwCurrentHeaders(self, headersDict):
        self.gpwCurrentSource.stockHeaders = headersDict
        self.stockHeadersChanged.emit()
