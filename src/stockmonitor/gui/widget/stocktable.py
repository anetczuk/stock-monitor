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

from PyQt5 import QtCore
from PyQt5.QtCore import QModelIndex
from PyQt5.QtWidgets import QMenu, QAction, QInputDialog
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QCursor
from PyQt5.QtGui import QDesktopServices

from stockmonitor.gui.widget.dataframetable import DataFrameTable, TableRowColorDelegate
from stockmonitor.gui.dataobject import DataObject


_LOGGER = logging.getLogger(__name__)


class StockTable( DataFrameTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("stocktable")
        self.dataObject = None

    def connectData(self, dataObject):
        self.dataObject = dataObject

    def contextMenuEvent( self, _ ):
        contextMenu = self.createContextMenu()
        globalPos = QCursor.pos()
        contextMenu.exec_( globalPos )

    def createContextMenu(self):
        contextMenu         = QMenu(self)
        if self.dataObject is not None:
            stockInfoMenu = contextMenu.addMenu("Stock info")
            gpwLinks = self._getGpwInfoLinks()
            if gpwLinks:
                action = self._createActionOpenUrl("gpw.pl", gpwLinks)
                action.setParent( stockInfoMenu )
                stockInfoMenu.addAction( action )
            moneyLinks = self._getMoneyInfoLinks()
            if moneyLinks:
                action = self._createActionOpenUrl("money.pl", moneyLinks)
                action.setParent( stockInfoMenu )
                stockInfoMenu.addAction( action )
            googleLinks = self._getGoogleInfoLinks()
            if googleLinks:
                action = self._createActionOpenUrl("google.pl", googleLinks)
                action.setParent( stockInfoMenu )
                stockInfoMenu.addAction( action )
        self._addFavActions( contextMenu )
        contextMenu.addSeparator()
        filterDataAction    = contextMenu.addAction("Filter data")
        configColumnsAction = contextMenu.addAction("Configure columns")

        filterDataAction.triggered.connect( self.showFilterConfiguration )
        configColumnsAction.triggered.connect( self.showColumnsConfiguration )

        if self._rawData is None:
            configColumnsAction.setEnabled( False )

        return contextMenu

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

    def _addFavActions(self, contextMenu):
        favsActions = []
        if self.dataObject is not None:
            favSubMenu    = contextMenu.addMenu("Add to favs")
            favGroupsList = self.dataObject.favs.getFavGroups()
            for favGroup in favGroupsList:
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
        favList = self._getSelectedTickers()
        self.dataObject.addFav( favGrp, favList )

    def _getGpwInfoLinks(self):
        favList = self._getSelectedTickers()
        if not favList:
            _LOGGER.warning( "unable to get stock info: empty ticker list" )
            return []
        dataAccess = self.dataObject.gpwCurrentData
        ret = []
        for ticker in favList:
            isin = self.dataObject.getStockIsinFromTicker( ticker )
            if isin is None:
                continue
            infoLink = dataAccess.getGpwLinkFromIsin( isin )
            if infoLink is not None:
                ret.append( infoLink )
        _LOGGER.debug( "returning links list: %s", ret )
        return ret

    def _getMoneyInfoLinks(self):
        favList = self._getSelectedTickers()
        if not favList:
            _LOGGER.warning( "unable to open stock info: empty ticker list" )
            return []
        dataAccess = self.dataObject.gpwCurrentData
        ret = []
        for ticker in favList:
            isin = self.dataObject.getStockIsinFromTicker( ticker )
            if isin is None:
                continue
            infoLink = dataAccess.getMoneyLinkFromIsin( isin )
            if infoLink is not None:
                ret.append( infoLink )
        _LOGGER.debug( "returning links list: %s", ret )
        return ret

    def _getGoogleInfoLinks(self):
        favList = self._getSelectedTickers()
        if not favList:
            _LOGGER.warning( "unable to get stock info: empty ticker list" )
            return []
        dataAccess = self.dataObject.gpwCurrentData
        ret = []
        for ticker in favList:
            infoLink = dataAccess.getGoogleLinkFromTicker( ticker )
            if infoLink is not None:
                ret.append( infoLink )
        _LOGGER.debug( "returning links list: %s", ret )
        return ret

    ## returns list of tickers
    def _getSelectedTickers(self) -> List[str]:
        ## reimplement if needed
        return list()


## ====================================================================


class StockFullColorDelegate( TableRowColorDelegate ):

    def __init__(self, dataObject: DataObject):
        self.dataObject = dataObject

#     def foreground(self, index: QModelIndex ):
#         ## reimplement if needed
#         return None

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
        dataAccess = self.dataObject.gpwCurrentData
        dataframe = dataAccess.getWorksheet( False )
        self.setData( dataframe )

    def updateView(self):
        self.setHeadersText( self.dataObject.gpwCurrentHeaders )

    def _getSelectedTickers(self):
        return self.getSelectedData( 3 )                ## ticker

    def settingsAccepted(self):
        self.dataObject.gpwCurrentHeaders = self.pandaModel.customHeader

    def settingsRejected(self):
        self.dataObject.gpwCurrentHeaders = self.pandaModel.customHeader


## ====================================================================


class StockFavsTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("stockfavstable")
        self.dataObject = None
        self.favGroup = None

    # pylint: disable=W0221
    def connectData(self, dataObject, favGroup):
        self.dataObject = dataObject
        self.favGroup = favGroup
        if self.dataObject is None:
            return
        self.dataObject.stockDataChanged.connect( self.updateData )
        self.dataObject.stockHeadersChanged.connect( self.updateView )
        self.updateData()
        self.updateView()

    def updateData(self):
        dataframe = self.dataObject.getFavStock( self.favGroup )
        self.setData( dataframe )

    def updateView(self):
        self.setHeadersText( self.dataObject.gpwCurrentHeaders )

    def createContextMenu(self):
        contextMenu = super().createContextMenu()
        if self.dataObject is not None:
            remFavAction = insert_new_action(contextMenu, "Remove fav", 1)
            remFavAction.triggered.connect( self._removeFav )
        return contextMenu

    def _removeFav(self):
        favList = self._getSelectedTickers()
        self.dataObject.deleteFav( self.favGroup, favList )

    def _getSelectedTickers(self):
        return self.getSelectedData( 3 )                ## ticker

    def settingsAccepted(self):
        self.dataObject.gpwCurrentHeaders = self.pandaModel.customHeader

    def settingsRejected(self):
        self.dataObject.gpwCurrentHeaders = self.pandaModel.customHeader


## ====================================================================


class ToolStockTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("toolstocktable")

    def _getSelectedTickers(self):
        dataAccess = self.dataObject.gpwCurrentData
        selectedData = self.getSelectedData( 0 )                ## stock name
        tickersList = set()
        for stockName in selectedData:
            ticker = dataAccess.getTickerFieldByName( stockName )
            if ticker is not None:
                tickersList.add( ticker )
        return list( tickersList )


def stock_background_color( dataObject, ticker ):
    walletStock = dataObject.wallet.getCurrentStock()
    if ticker in walletStock:
        return TableRowColorDelegate.STOCK_WALLET_BGCOLOR

    allFavs = dataObject.favs.getFavsAll()
    if ticker in allFavs:
        return TableRowColorDelegate.STOCK_FAV_BGCOLOR

    return None


def insert_new_action( menu: QMenu, text: str, index: int ):
    actionsList = menu.actions()
    if index >= len( actionsList ):
        return menu.addAction( text )
    indexAction = actionsList[index]
    newAction = QAction( text, menu )
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
