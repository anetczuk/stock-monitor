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
from PyQt5.QtWidgets import QMenu, QInputDialog
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QCursor
from PyQt5.QtGui import QDesktopServices

from stockmonitor.gui.widget.dataframetable import DataFrameTable


_LOGGER = logging.getLogger(__name__)


class StockTable( DataFrameTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("stocktable")


## ====================================================================


class DataStockTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.dataObject = None

    def connectData(self, dataObject):
        self.dataObject = dataObject

    def contextMenuEvent( self, _ ):
        contextMenu         = QMenu(self)
        stockInfoAction = contextMenu.addAction("Stock info")
        favsActions = self._addFavActions( contextMenu )
        contextMenu.addSeparator()

        filterDataAction = contextMenu.addAction("Filter data")
        configColumnsAction = contextMenu.addAction("Configure columns")
        if self._rawData is None:
            configColumnsAction.setEnabled( False )

        globalPos = QCursor.pos()
        action = contextMenu.exec_( globalPos )

        if action == configColumnsAction:
            self.showColumnsConfiguration()
        elif action == filterDataAction:
            self.showFilterConfiguration()
        elif action in favsActions:
            favGroup = action.data()
            self._addToFav( favGroup )
        elif action == stockInfoAction:
            self._openInfo()

    def _addFavActions(self, contextMenu):
        favsActions = []
        if self.dataObject is not None:
            favSubMenu    = contextMenu.addMenu("Add to favs")
            favGroupsList = self.dataObject.favs.favGroupsList()
            for favGroup in favGroupsList:
                favAction = favSubMenu.addAction( favGroup )
                favAction.setData( favGroup )
                favsActions.append( favAction )
            newFavGroupAction = favSubMenu.addAction( "New group ..." )
            newFavGroupAction.setData( None )
            favsActions.append( newFavGroupAction )
        return favsActions

    def _addToFav(self, favGrp):
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
        favList = self._getSelectedCodes()
        self.dataObject.addFav( favGrp, favList )

    def _openInfo(self):
        dataAccess = self.dataObject.gpwCurrentData
        favList = self._getSelectedCodes()
        for code in favList:
            infoLink = dataAccess.getInfoLinkFromCode( code )
            url = QtCore.QUrl(infoLink)
            _LOGGER.info( "opening url: %s", url )
            QDesktopServices.openUrl( url )

    def _getSelectedCodes(self) -> List[str]:
        ## reimplement if needed
        return list()


## ====================================================================


class StockFullTable( DataStockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("stockfulltable")

    def connectData(self, dataObject):
        super().connectData( dataObject )
        self.dataObject = dataObject
        self.dataObject.stockDataChanged.connect( self.updateData )
        self.dataObject.stockHeadersChanged.connect( self.updateView )
        self.updateData()
        self.updateView()

    def updateData(self):
        dataAccess = self.dataObject.gpwCurrentData
        dataframe = dataAccess.getWorksheet( False )
        self.setData( dataframe )

    def updateView(self):
        self.setHeadersText( self.dataObject.gpwCurrentHeaders )

    def _getSelectedCodes(self):
        dataAccess = self.dataObject.gpwCurrentData
        selection = self.selectionModel()
        indexes = selection.selectedIndexes()
        favCodes = set()
        for ind in indexes:
            sourceIndex = self.model().mapToSource( ind )
            dataRow = sourceIndex.row()
            code = dataAccess.getShortField( dataRow )
            favCodes.add( code )
        favList = list(favCodes)
        return favList

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

    def contextMenuEvent( self, _ ):
        contextMenu         = QMenu(self)
        stockInfoAction     = contextMenu.addAction("Stock info")
        remFavAction        = contextMenu.addAction("Remove fav")
        contextMenu.addSeparator()
        filterDataAction = contextMenu.addAction("Filter data")
        configColumnsAction = contextMenu.addAction("Configure columns")

        globalPos = QCursor.pos()
        action = contextMenu.exec_( globalPos )

        if action == configColumnsAction:
            self.showColumnsConfiguration()
        elif action == filterDataAction:
            self.showFilterConfiguration()
        elif action == remFavAction:
            favList = self._getSelectedCodes()
            self.dataObject.deleteFav( self.favGroup, favList )
        elif action == stockInfoAction:
            self._openInfo()

    def _openInfo(self):
        dataAccess = self.dataObject.gpwCurrentData
        favList = self._getSelectedCodes()
        for code in favList:
            infoLink = dataAccess.getInfoLinkFromCode( code )
            url = QtCore.QUrl( infoLink )
            _LOGGER.info( "opening url: %s", url )
            QDesktopServices.openUrl( url )

    def _getSelectedCodes(self):
        dataAccess = self.dataObject.gpwCurrentData
        selection = self.selectionModel()
        indexes = selection.selectedIndexes()
        favCodes = set()
        for ind in indexes:
            sourceIndex = self.model().mapToSource( ind )
            dataRow = sourceIndex.row()
            code = dataAccess.getShortFieldFromData( self._rawData, dataRow )
            favCodes.add( code )
        favList = list(favCodes)
        return favList

    def settingsAccepted(self):
        self.dataObject.gpwCurrentHeaders = self.pandaModel.customHeader

    def settingsRejected(self):
        self.dataObject.gpwCurrentHeaders = self.pandaModel.customHeader


## ====================================================================


class ToolStockTable( DataStockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("toolstocktable")

    def _getSelectedCodes(self):
        dataAccess = self.dataObject.gpwCurrentData
        selection = self.selectionModel()
        indexes = selection.selectedIndexes()
        favCodes = set()
        for ind in indexes:
            sourceIndex = self.model().mapToSource( ind )
            dataRow = sourceIndex.row()
            stockName = self._rawData.iloc[dataRow, 0]
            code = dataAccess.getShortFieldByName( stockName )
            if code is not None:
                favCodes.add( code )
        favList = list(favCodes)
        return favList
