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

from typing import List

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QModelIndex
from PyQt5.QtWidgets import QMenu, QAction, QInputDialog
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QCursor
from PyQt5.QtGui import QDesktopServices

from stockdataaccess.dataaccess.datatype import StockDataType
from stockdataaccess.dataaccess.gpw.gpwcurrentdata import GpwCurrentStockData

from stockmonitor.datatypes.datatypes import MarkerEntry
from stockmonitor.gui.dataobject import DataObject, READONLY_FAV_GROUPS
from stockmonitor.gui.widget.dataframetable import DataFrameTable, TableRowColorDelegate
from stockmonitor.gui.widget import stockchartwidget, stockmosaicwidget
from stockmonitor.gui.widget import indexchartwidget


_LOGGER = logging.getLogger(__name__)


class StockTable( DataFrameTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("stocktable")
        self.dataObject: DataObject = None

    def connectData(self, dataObject):
        self.dataObject = dataObject

    def contextMenuEvent( self, event ):
        evPos  = event.pos()
        mIndex = self.indexAt( evPos )
        contextMenu = self.createContextMenu( mIndex )
        globalPos = QCursor.pos()
        contextMenu.exec_( globalPos )

    def createContextMenu(self, _):
#     def createContextMenu(self, itemIndex):
        contextMenu = QMenu(self)

        if self.dataObject is not None:
            self._addOpenChartAction( contextMenu )

            stockSummaryAction = contextMenu.addAction("Stock summary")
            isinsList = self._getSelectedIsins()
            stockSummaryAction.setData( isinsList )
            stockSummaryAction.triggered.connect( self._stockSummaryAction )

            gpwLinks     = self._getGpwInfoLinks()
            bankierLinks = self._getBankierInfoLinks()
            moneyLinks   = self._getMoneyInfoLinks()
            googleLinks  = self._getGoogleInfoLinks()
            if gpwLinks or moneyLinks or googleLinks or bankierLinks:
                stockInfoMenu = contextMenu.addMenu("Stock info")
                if gpwLinks:
                    action = self._createActionOpenUrl("gpw.pl", gpwLinks)
                    action.setParent( stockInfoMenu )
                    stockInfoMenu.addAction( action )
                if bankierLinks:
                    action = self._createActionOpenUrl("bankier.pl", bankierLinks)
                    action.setParent( stockInfoMenu )
                    stockInfoMenu.addAction( action )
                if moneyLinks:
                    action = self._createActionOpenUrl("money.pl", moneyLinks)
                    action.setParent( stockInfoMenu )
                    stockInfoMenu.addAction( action )
                if googleLinks:
                    action = self._createActionOpenUrl("google.pl", googleLinks)
                    action.setParent( stockInfoMenu )
                    stockInfoMenu.addAction( action )

        tickersList = self._getSelectedTickers()
        if tickersList:
            self._addFavActions( contextMenu )

            markersSubMenu = contextMenu.addMenu("Add to markers")
            markersBuyAction = markersSubMenu.addAction( "Buy" )
            markersBuyAction.setData( MarkerEntry.OperationType.BUY )
            markersBuyAction.triggered.connect( self._addToMarkersAction )
            markersBuyAction = markersSubMenu.addAction( "Sell" )
            markersBuyAction.setData( MarkerEntry.OperationType.SELL )
            markersBuyAction.triggered.connect( self._addToMarkersAction )

        contextMenu.addSeparator()

        clearSortingAction  = contextMenu.addAction("Clear sorting")
        filterDataAction    = contextMenu.addAction("Filter data")
        configColumnsAction = contextMenu.addAction("Configure columns")

        clearSortingAction.triggered.connect( self.clearSorting )
        filterDataAction.triggered.connect( self.showFilterConfiguration )
        configColumnsAction.triggered.connect( self.showColumnsConfiguration )

        if self._rawData is None:
            configColumnsAction.setEnabled( False )

        return contextMenu

    def _stockSummaryAction(self):
        # ugly but prevents circular dependency
        from stockmonitor.gui.widget.stocksummarywidget import create_window as stocksummary_create_window

        if self.dataObject is None:
            return
        parentAction = self.sender()
        isinList = parentAction.data()
        if is_iterable( isinList ) is False:
            isinList = list( isinList )
        for isin in isinList:
            stocksummary_create_window( self.dataObject, isin, self )

    def _createActionOpenUrl(self, text, link ):
        action = QAction( text )
        action.setData( link )
        action.triggered.connect( self._openUrlAction )
        return action

    def _openUrlAction(self):
        parentAction = self.sender()
        urlLinkList = parentAction.data()
        if is_iterable( urlLinkList ) is False:
            urlLinkList = list( urlLinkList )
        for urlLink in urlLinkList:
            url = QtCore.QUrl(urlLink)
            _LOGGER.info( "opening url: %s", url )
            QDesktopServices.openUrl( url )

    def _addOpenChartAction(self, contextMenu):
        tickersList = self._getSelectedTickers()
        if not tickersList:
            return
        openChartMenu = contextMenu.addAction("Open chart")
        openChartMenu.setData( tickersList )
        openChartMenu.triggered.connect( self._openChartAction )

        openMosaicMenu = contextMenu.addAction("Open mosaic")
        openMosaicMenu.setData( tickersList )
        openMosaicMenu.triggered.connect( self._openMosaicAction )

    def _openChartAction(self):
        if self.dataObject is None:
            return
        parentAction = self.sender()
        tickerList = parentAction.data()
        if is_iterable( tickerList ) is False:
            tickerList = list( tickerList )
        for ticker in tickerList:
            stockchartwidget.create_window( self.dataObject, ticker, self )

    def _openMosaicAction(self):
        if self.dataObject is None:
            return
        parentAction = self.sender()
        tickerList = parentAction.data()
        if is_iterable( tickerList ) is False:
            tickerList = list( tickerList )
        stockmosaicwidget.create_window( self.dataObject, tickerList, self )

    def _addFavActions(self, contextMenu):
        favsActions = []
        if self.dataObject is None:
            return favsActions
        favSubMenu    = contextMenu.addMenu("Add to favs")
        favGroupsList = self.dataObject.favs.getFavGroups()
        for favGroup in favGroupsList:
            if favGroup in READONLY_FAV_GROUPS:
                continue
            favAction = favSubMenu.addAction( favGroup )
            favAction.setData( favGroup )
            favAction.triggered.connect( self._addToFavAction )
            favsActions.append( favAction )
        newFavGroupAction = favSubMenu.addAction( "New group ..." )
        newFavGroupAction.setData( None )
        newFavGroupAction.triggered.connect( self._addToFavAction )
        favsActions.append( newFavGroupAction )
        return favsActions

    def _addToFavAction(self):
        parentAction = self.sender()
        favGrp = parentAction.data()
        if favGrp is None:
            newText, ok = QInputDialog.getText( self,
                                                "Rename Fav Group",
                                                "Fav Group name:",
                                                QLineEdit.Normal,
                                                "Favs" )
            if ok and newText:
                # not empty
                favGrp = newText
            else:
                return
        if favGrp in READONLY_FAV_GROUPS:
            return
        tickersList = self._getSelectedTickers()
        self.dataObject.addFav( favGrp, tickersList )

    def _addToMarkersAction(self):
        parentAction = self.sender()
        markerOperation = parentAction.data()
        tickersList = self._getSelectedTickers()
        self.dataObject.addMarkersList( tickersList, markerOperation )

    def _getGpwInfoLinks(self):
        isinsList = self._getSelectedIsins()
        if not isinsList:
            _LOGGER.warning( "unable to get stock info: empty isin list" )
            return []
        dataAccess = self.dataObject.gpwCurrentData
        ret = []
        for isin in isinsList:
            if isin is None:
                continue
            infoLink = dataAccess.getGpwLinkFromIsin( isin )
            if infoLink is not None:
                ret.append( infoLink )
        _LOGGER.debug( "returning links list: %s", ret )
        return ret

    def _getMoneyInfoLinks(self):
        isinsList = self._getSelectedIsins()
        if not isinsList:
            _LOGGER.warning( "unable to open stock info: empty ticker list" )
            return []
        dataAccess = self.dataObject.gpwCurrentData
        ret = []
        for isin in isinsList:
            if isin is None:
                continue
            infoLink = dataAccess.getMoneyLinkFromIsin( isin )
            if infoLink is not None:
                ret.append( infoLink )
        _LOGGER.debug( "returning links list: %s", ret )
        return ret

    def _getGoogleInfoLinks(self):
        tickerList = self._getSelectedTickers()
        if not tickerList:
            _LOGGER.warning( "unable to get stock info: empty ticker list" )
            return []
        dataAccess = self.dataObject.gpwCurrentData
        ret = []
        for ticker in tickerList:
            infoLink = dataAccess.getGoogleLinkFromTicker( ticker )
            if infoLink is not None:
                ret.append( infoLink )
        _LOGGER.debug( "returning links list: %s", ret )
        return ret

    def _getBankierInfoLinks(self):
        nameList = self._getSelectedNames()
        if not nameList:
            _LOGGER.warning( "unable to open stock info: empty ticker list" )
            return []
        dataAccess = self.dataObject.gpwCurrentData
        ret = []
        for name in nameList:
            if name is None:
                continue
            infoLink = dataAccess.getBankierLinkFromName( name )
            if infoLink is not None:
                ret.append( infoLink )
        _LOGGER.debug( "returning links list: %s", ret )
        return ret

    ## returns list of tickers
    def _getSelectedTickers(self) -> List[str]:                         # pylint: disable=R0201
        ## reimplement if needed
        return []

    ## returns list of tickers
    def _getSelectedNames(self) -> List[str]:                         # pylint: disable=R0201
        ## reimplement if needed
        tickerList = self._getSelectedTickers()
        if not tickerList:
            _LOGGER.warning( "unable to open stock info: empty ticker list" )
            return []
        ret = []
        for ticker in tickerList:
            name = self.dataObject.getNameFromTicker( ticker )
            if name is None:
                continue
            ret.append( name )
        return ret

    ## returns list of isins
    def _getSelectedIsins(self) -> List[str]:
        ## reimplement if needed
        tickerList = self._getSelectedTickers()
        if not tickerList:
            _LOGGER.warning( "unable to open stock info: empty ticker list" )
            return []
        ret = []
        for ticker in tickerList:
            isin = self.dataObject.getStockIsinFromTicker( ticker )
            if isin is None:
                continue
            ret.append( isin )
        return ret


## ====================================================================


class StockFullColorDelegate( TableRowColorDelegate ):

    def __init__(self, dataObject: DataObject):
        super().__init__()
        self.dataObject = dataObject

    ## override
    def foreground(self, index: QModelIndex ):
        dataColumn = index.column()
        ## "Zm.do k.odn.[%]"
        dataIndex = GpwCurrentStockData.getColumnIndex( StockDataType.CHANGE_TO_REF )
        if dataColumn == dataIndex:
            stockChangeString = index.data()
            if stockChangeString != "-":
                stockChange = float(stockChangeString)
                if stockChange > 0.0:
                    return QtGui.QColor( "green" )
    #             return QtGui.QColor( "red" )
        return None

    def background(self, index: QModelIndex ):
        dataRow = index.row()
        ticker = self.dataObject.getTicker( dataRow )
        return stock_background_color( self.dataObject, ticker )


class StockFullTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("stockfulltable")
        self.setShowGrid( True )
        self.setAlternatingRowColors( False )

    def connectData(self, dataObject):
        super().connectData( dataObject )

        colorDecorator = StockFullColorDelegate( self.dataObject )
        self.setColorDelegate( colorDecorator )

        self.dataObject.stockDataChanged.connect( self.updateData )
        self.dataObject.stockHeadersChanged.connect( self.updateView )
        self.updateView()

    def updateData(self):
        dataAccess: GpwCurrentStockData = self.dataObject.gpwCurrentData
        dataframe = dataAccess.getWorksheetData( False )
        self.setData( dataframe )

    def updateView(self):
        self.setHeadersText( self.dataObject.gpwCurrentHeaders )

    def _getSelectedTickers(self):
        dataIndex = GpwCurrentStockData.getColumnIndex( StockDataType.TICKER )
        return self.getSelectedData( dataIndex )                ## ticker

    def settingsAccepted(self):
        if self.dataObject is not None:
            self.dataObject.gpwCurrentHeaders = self.pandaModel.customHeader

    def settingsRejected(self):
        if self.dataObject is not None:
            self.dataObject.gpwCurrentHeaders = self.pandaModel.customHeader


## ====================================================================


class StockIndexesTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("stockindexestable")
#         self.setShowGrid( True )
#         self.setAlternatingRowColors( False )

#     def connectData(self, dataObject):
#         super().connectData( dataObject )
#
#         colorDecorator = ToolStockColorDelegate( self.dataObject )
#         self.setColorDelegate( colorDecorator )

    ## override
    def createContextMenu(self, _):
        contextMenu = QMenu(self)

        if self.dataObject is not None:
            self._addOpenChartAction( contextMenu )

            gpwLinks = self._getGpwInfoLinks()
            moneyLinks = self._getMoneyInfoLinks()
            googleLinks = self._getGoogleInfoLinks()
            if gpwLinks or moneyLinks or googleLinks:
                stockInfoMenu = contextMenu.addMenu("Stock info")
                if gpwLinks:
                    action = self._createActionOpenUrl("gpw.pl", gpwLinks)
                    action.setParent( stockInfoMenu )
                    stockInfoMenu.addAction( action )
                if moneyLinks:
                    action = self._createActionOpenUrl("money.pl", moneyLinks)
                    action.setParent( stockInfoMenu )
                    stockInfoMenu.addAction( action )
                if googleLinks:
                    action = self._createActionOpenUrl("google.pl", googleLinks)
                    action.setParent( stockInfoMenu )
                    stockInfoMenu.addAction( action )

        contextMenu.addSeparator()

        clearSortingAction  = contextMenu.addAction("Clear sorting")
        filterDataAction    = contextMenu.addAction("Filter data")
        configColumnsAction = contextMenu.addAction("Configure columns")

        clearSortingAction.triggered.connect( self.clearSorting )
        filterDataAction.triggered.connect( self.showFilterConfiguration )
        configColumnsAction.triggered.connect( self.showColumnsConfiguration )

        if self._rawData is None:
            configColumnsAction.setEnabled( False )

        return contextMenu

    def _addOpenChartAction(self, contextMenu):
        isinList = self._getSelectedIsins()
        if not isinList:
            return
        openChartMenu = contextMenu.addAction("Open chart")
        openChartMenu.setData( isinList )
        openChartMenu.triggered.connect( self._openChartAction )

    def _openChartAction(self):
        if self.dataObject is None:
            return
        parentAction = self.sender()
        isinList = parentAction.data()
        if is_iterable( isinList ) is False:
            isinList = list( isinList )
        for isin in isinList:
            indexchartwidget.create_window( self.dataObject, isin, self )

    ## override
    def _getGpwInfoLinks(self):
        isinsList = self._getSelectedIsins()
        if not isinsList:
            _LOGGER.warning( "unable to get stock info: empty isin list" )
            return []
        dataAccess = self.dataObject.gpwIndexesData
        ret = []
        for isin in isinsList:
            if isin is None:
                continue
            infoLink = dataAccess.getGpwLinkFromIsin( isin )
            if infoLink is not None:
                ret.append( infoLink )
        _LOGGER.debug( "returning links list: %s", ret )
        return ret

    ## override
    def _getMoneyInfoLinks(self):
        selectedList = self._getSelectedNames()
        if not selectedList:
            _LOGGER.warning( "unable to open stock info: empty ticker list" )
            return []
        dataAccess = self.dataObject.gpwIndexesData
        ret = []
        for item in selectedList:
            if item is None:
                continue
            infoLink = dataAccess.getMoneyLinkFromName( item )
            if infoLink is not None:
                ret.append( infoLink )
        _LOGGER.debug( "returning links list: %s", ret )
        return ret

    ## override
    def _getGoogleInfoLinks(self):
        selectedList = self._getSelectedNames()
        if not selectedList:
            _LOGGER.warning( "unable to get stock info: empty ticker list" )
            return []
        dataAccess = self.dataObject.gpwIndexesData
        ret = []
        for item in selectedList:
            infoLink = dataAccess.getGoogleLinkFromName( item )
            if infoLink is not None:
                ret.append( infoLink )
        _LOGGER.debug( "returning links list: %s", ret )
        return ret

    def _getSelectedNames(self):
        selectedData = self.getSelectedData( 1 )                ## skrot
        retList = set()
        for stockName in selectedData:
            retList.add( stockName )
        return list( retList )

    ## returns list of isins
    ## override
    def _getSelectedIsins(self) -> List[str]:
        selectedData = self.getSelectedData( 12 )                ## isin
        return list( selectedData )


## ====================================================================


class ToolStockColorDelegate( TableRowColorDelegate ):

    def __init__(self, dataObject: DataObject):
        super().__init__()
        self.dataObject = dataObject

#     def foreground(self, index: QModelIndex ):
#         ## reimplement if needed
#         return None

    def background(self, index: QModelIndex ):
        sourceParent = index.parent()
        dataRow = index.row()
        dataIndex = self.parent.index( dataRow, 0, sourceParent )       ## get name
        name = dataIndex.data()
        ticker = self.dataObject.getTickerFromName( name )
        return stock_background_color( self.dataObject, ticker )


class ToolStockProxyModel( QtCore.QSortFilterProxyModel ):

    def __init__(self, parentObject=None):
        super().__init__(parentObject)

        ## 0 - no limitation
        ## 1 - limit to favs
        ## 2 - limit to wallet
        self._limitResults = 0

    def limitResults(self, state):
        self._limitResults = state
        self.invalidateFilter()

    def filterAcceptsRow( self, sourceRow, sourceParent ):
        if self._limitResults == 0:
            return True

        valueIndex = self.sourceModel().index( sourceRow, 0, sourceParent )
        rawValue = self.sourceModel().data( valueIndex, QtCore.Qt.UserRole )

        dataObject = self.parent().dataObject
        ticker = dataObject.getTickerFromName( rawValue )

        if self._limitResults == 1:
            allFavsSet = dataObject.getAllFavs()
            return ticker in allFavsSet

        if self._limitResults == 2:
            walletStock = dataObject.wallet.getCurrentStock()
            return ticker in walletStock

        return True


class ToolStockTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("toolstocktable")
        self.setShowGrid( True )
        self.setAlternatingRowColors( False )

        self.stockFilter = ToolStockProxyModel( self )
        self.addProxyModel( self.stockFilter )

    def connectData(self, dataObject):
        super().connectData( dataObject )

        colorDecorator = ToolStockColorDelegate( self.dataObject )
        self.setColorDelegate( colorDecorator )

        self.limitResults( 0 )

    def limitResults(self, state):
        self.stockFilter.limitResults( state )

    def _getSelectedTickers(self):
        if self.dataObject is None:
            _LOGGER.warning("no dataobject present (set to None)")
            return []
        dataAccess = self.dataObject.gpwCurrentSource.stockData
        selectedData = self.getSelectedData( 0 )                ## stock name
        tickersList = set()
        for stockName in selectedData:
            ticker = dataAccess.getTickerFieldByName( stockName )
            if ticker is not None:
                tickersList.add( ticker )
        return list( tickersList )


# =========================================================================


def wallet_background_color( dataObject, ticker ):
    walletStock = dataObject.wallet.getCurrentStock()
    if ticker in walletStock:
        return TableRowColorDelegate.STOCK_WALLET_BGCOLOR
    return None


def marker_background_color( dataObject: DataObject, ticker ):
    currentStock: GpwCurrentStockData = dataObject.gpwCurrentData
    recentValue = currentStock.getRecentValueByTicker( ticker )
    if recentValue is None:
        return None
    if recentValue == "-":
        return None
    markerColor = dataObject.markers.getBestMatchingColor( ticker, recentValue )
    if markerColor is not None:
        return QtGui.QColor( markerColor )
    return None


def stock_background_color( dataObject, ticker ):
    markerColor = marker_background_color( dataObject, ticker )
    if markerColor is not None:
        return markerColor

    walletColor = wallet_background_color( dataObject, ticker )
    if walletColor is not None:
        return walletColor

    allFavs = dataObject.favs.getFavsAll()
    if ticker in allFavs:
        return TableRowColorDelegate.STOCK_FAV_BGCOLOR

    return None


def insert_new_action( menu: QMenu, text: str, index: int ):
    actionsList = menu.actions()
    if index >= len( actionsList ):
        if text:
            return menu.addAction( text )
        return menu.addSeparator()
    indexAction = actionsList[index]
    if text:
        newAction = QAction( text, menu )
        menu.insertAction( indexAction, newAction )
    else:
        newAction = QAction( menu )
        newAction.setSeparator( True )
        menu.insertAction( indexAction, newAction )
    return newAction


def is_iterable(obj):
    try:
        iter(obj)
    # pylint: disable=W0703
    except Exception:
        return False
    else:
        return True
