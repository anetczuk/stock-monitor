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

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QCursor, QDesktopServices

from stockmonitor.gui.dataobject import READONLY_FAV_GROUPS
from stockmonitor.gui.widget import stockchartwidget
from stockmonitor.gui.widget import stocktable

from .. import uiloader


_LOGGER = logging.getLogger(__name__)


DetailsUiClass, DetailsBaseClass = uiloader.load_ui_from_module_path( "widget/espidetails" )


class ESPIDetails( DetailsBaseClass ):                      # type: ignore

    resized = QtCore.pyqtSignal()

    def __init__(self, dataRow, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = DetailsUiClass()
        self.ui.setupUi(self)

        self.ui.company.setOpenExternalLinks(True)
        self.ui.company.setUrl( dataRow["url"], dataRow["name"] )
        self.ui.company.adjustSize()
        self.ui.date.setText( str( dataRow["date"] ) )

        self.ui.title.setText( dataRow["title"] )
        self.ui.title.viewport().setAutoFillBackground(False)
        self.ui.title.adjustSize()

    def adjustHeight(self):
        docSize = self.ui.title.document()
        self.ui.title.setFixedHeight( docSize.size().height() + 3 )
        self.resized.emit()

    def showEvent( self, _ ):
#     def showEvent( self, event ):
        QtCore.QTimer.singleShot( 50, self.adjustHeight )


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class ESPIListWidget( QtBaseClass ):                        # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.dataObject = None

        self.ui.messagesNumSB.valueChanged.connect( self._setMessagesLimit )

    def connectData(self, dataObject):
        self.dataObject = dataObject
        self.dataObject.stockDataChanged.connect( self.updateView )
        self.dataObject.favsChanged.connect( self.updateView )
        self.dataObject.walletDataChanged.connect( self.updateView )

    def updateView(self):
        self.ui.espiList.clear()
        if self.dataObject is None:
            _LOGGER.warning("unable to update view")
            return
        espiData = self.dataObject.gpwESPIData
        if espiData is None:
            _LOGGER.info("no data to view")
            return
        dataFrame = espiData.getWorksheet()
        if dataFrame is None:
            _LOGGER.info("no data to view")
            return

        _LOGGER.info("updating view")
        for _, row in dataFrame.iterrows():
            self.addItem( row )

    def addItem(self, row):
        item = QtWidgets.QListWidgetItem()
        details = ESPIDetails( row, self )
        details.resized.connect( lambda: item.setSizeHint( details.sizeHint() ) )

        ticker = self.dataObject.getTickerFromIsin( row["isin"] )
        bgColor = stocktable.stock_background_color( self.dataObject, ticker )
        if bgColor is not None:
            item.setBackground( bgColor )

        self.ui.espiList.addItem( item )
        self.ui.espiList.setItemWidget( item, details )

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Enter or event.key() == QtCore.Qt.Key_Return:
            self.openLink()

    def openLink(self):
        row = self._currentRow()
        urlLink = row["url"]
        url = QtCore.QUrl(urlLink)
        QDesktopServices.openUrl( url )

    def contextMenuEvent( self, _ ):
        contextMenu = self.createContextMenu()
        if contextMenu is None:
            return
        globalPos = QCursor.pos()
        contextMenu.exec_( globalPos )

    def createContextMenu(self):
        if self.dataObject is None:
            return None

        contextMenu = QtWidgets.QMenu(self)
        openChartMenu = contextMenu.addAction("Open chart")
        openChartMenu.triggered.connect( self._openChartAction )

        isin = self._currentISIN()
        dataAccess = self.dataObject.gpwCurrentData
        gpwLink    = dataAccess.getGpwLinkFromIsin( isin )
        moneyLink  = dataAccess.getMoneyLinkFromIsin( isin )
        ticker     = self.dataObject.getTickerFromIsin( isin )
        googleLink = dataAccess.getGoogleLinkFromTicker( ticker )

        if gpwLink or moneyLink or googleLink:
            stockInfoMenu = contextMenu.addMenu("Stock info")
            if gpwLink:
                action = self._createActionOpenUrl("gpw.pl", [gpwLink])
                action.setParent( stockInfoMenu )
                stockInfoMenu.addAction( action )
            if moneyLink:
                action = self._createActionOpenUrl("money.pl", [moneyLink])
                action.setParent( stockInfoMenu )
                stockInfoMenu.addAction( action )
            if googleLink:
                action = self._createActionOpenUrl("google.pl", [googleLink])
                action.setParent( stockInfoMenu )
                stockInfoMenu.addAction( action )

        favSubMenu = contextMenu.addMenu("Add to favs")
        favGroupsList = self.dataObject.favs.getFavGroups()
        for favGroup in favGroupsList:
            if favGroup in READONLY_FAV_GROUPS:
                continue
            favAction = favSubMenu.addAction( favGroup )
            favAction.setData( favGroup )
            favAction.triggered.connect( self._addToFavAction )
        newFavGroupAction = favSubMenu.addAction( "New group ..." )
        newFavGroupAction.setData( None )
        newFavGroupAction.triggered.connect( self._addToFavAction )

        return contextMenu

    def _openChartAction(self):
        ticker = self._currentTicker()
        stockchartwidget.create_window( self.dataObject, ticker, self )

    def _addToFavAction(self):
        ticker = self._currentTicker()
        parentAction = self.sender()
        favGrp = parentAction.data()
        if favGrp is None:
            newText, ok = QtWidgets.QInputDialog.getText( self,
                                                          "Rename Fav Group",
                                                          "Fav Group name:",
                                                          QtWidgets.QLineEdit.Normal,
                                                          "Favs" )
            if ok and newText:
                # not empty
                favGrp = newText
            else:
                return
        if favGrp in READONLY_FAV_GROUPS:
            return
        self.dataObject.addFav( favGrp, [ticker] )

    def _createActionOpenUrl(self, text, link ):
        action = QtWidgets.QAction( text )
        action.setData( link )
        action.triggered.connect( self._openUrlAction )
        return action

    def _openUrlAction(self):
        parentAction = self.sender()
        urlLinkList = parentAction.data()
        if stocktable.is_iterable( urlLinkList ) is False:
            urlLinkList = list( urlLinkList )
        for urlLink in urlLinkList:
            url = QtCore.QUrl(urlLink)
            _LOGGER.info( "opening url: %s", url )
            QDesktopServices.openUrl( url )

    def _currentTicker(self):
        isin = self._currentISIN()
        return self.dataObject.getTickerFromIsin( isin )

    def _currentISIN(self):
        row = self._currentRow()
        isin = row["isin"]
        return isin

    def _currentRow(self):
        currentRow = self.ui.espiList.currentRow()
        espiData = self.dataObject.gpwESPIData
        dataFrame = espiData.getWorksheet()
        return dataFrame.iloc[ currentRow ]

    def _setMessagesLimit(self, limit):
        if self.dataObject is None:
            _LOGGER.warning("unable to set limit")
            return
        espiData = self.dataObject.gpwESPIData
        espiData.setLimit( limit )
