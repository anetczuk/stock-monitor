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

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QModelIndex
from PyQt5.QtWidgets import QFileDialog

from stockmonitor.dataaccess.transactionsloader import load_mb_transactions
from stockmonitor.gui.dataobject import DataObject
from stockmonitor.gui.widget.stocktable import StockTable
from stockmonitor.gui.widget.stocktable import marker_background_color
from stockmonitor.gui.widget.stocktable import insert_new_action, is_iterable
from stockmonitor.gui.widget.valuechartwidget import create_stockprofit_window,\
    create_wallet_profit_window, create_walletgain_window
from stockmonitor.gui.widget.dataframetable import TableRowColorDelegate

from .. import uiloader


_LOGGER = logging.getLogger(__name__)


class WalletProxyModel( QtCore.QSortFilterProxyModel ):

    def __init__(self, parentObject=None):
        super().__init__(parentObject)

        self._includeSoldOut = False

    def includeSoldOut(self, state=True):
        self._includeSoldOut = state
        self.invalidateFilter()

    def filterAcceptsRow( self, sourceRow, sourceParent ):
        if self._includeSoldOut:
            return True

        valueIndex = self.sourceModel().index( sourceRow, 2, sourceParent )
        rawValue = self.sourceModel().data( valueIndex, QtCore.Qt.UserRole )
        return rawValue > 0


## ====================================================================


class WalletColorDelegate( TableRowColorDelegate ):

    def __init__(self, dataObject: DataObject):
        super().__init__()
        self.dataObject = dataObject

    def foreground(self, index: QModelIndex ):
        dataColumn = index.column()
        ## "Zm.do k.odn.[%]" or "Zysk [%]"
        if dataColumn in (5, 9):
            stockChangeString = index.data()
            if stockChangeString != "-":
                stockChange = float(stockChangeString)
                if stockChange > 0.0:
                    return QtGui.QColor( "green" )
    #             return QtGui.QColor( "red" )
        return None

    def background(self, index: QModelIndex ):
        sourceParent = index.parent()
        dataRow = index.row()
        dataIndex = self.parent.index( dataRow, 1, sourceParent )       ## get ticker
        ticker = dataIndex.data()
        col = marker_background_color( self.dataObject, ticker )
        return col


## =================================================================


class WalletStockTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("walletstocktable")

    def connectData(self, dataObject):
        super().connectData( dataObject )

        colorDecorator = WalletColorDelegate( dataObject )
        self.setColorDelegate( colorDecorator )

    ## override
    def createContextMenu(self, itemIndex):
        contextMenu = super().createContextMenu( itemIndex )
        if self.dataObject is not None:
            tickersList = self._getSelectedTickers()
            if tickersList:
                profitChartAction = insert_new_action(contextMenu, "Open overall profit chart", 1)
                profitChartAction.setData( tickersList )
                profitChartAction.triggered.connect( self.openStockProfitChart )

#                 valueChartAction = insert_new_action(contextMenu, "Open value chart", 1)
#                 valueChartAction.setData( tickersList )
#                 valueChartAction.triggered.connect( self.openStockValueChart )

        return contextMenu

#     def openStockValueChart(self):
#         if self.dataObject is None:
#             return
#         parentAction = self.sender()
#         tickersList = parentAction.data()
#         if is_iterable( tickersList ) is False:
#             tickersList = list( tickersList )
#         for ticker in tickersList:
#             create_stockvalue_window( self.dataObject, ticker, self )

    def openStockProfitChart(self):
        if self.dataObject is None:
            return
        parentAction = self.sender()
        tickersList = parentAction.data()
        if is_iterable( tickersList ) is False:
            tickersList = list( tickersList )
        for ticker in tickersList:
            create_stockprofit_window( self.dataObject, ticker, self )

    def importTransactions(self):
        if self.dataObject is None:
            return
        filePath = QFileDialog.getOpenFileName( self, "Import transactions" )
        if not filePath:
            return
        dataPath = filePath[0]
        if not dataPath:
            return
        import_mb_transactions( self.dataObject, dataPath )

    def _getSelectedTickers(self):
        selectedData = self.getSelectedData( 1 )                ## ticker
        return selectedData


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class WalletWidget( QtBaseClass ):           # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.dataObject = None

        self.soldOutFilter = WalletProxyModel()
        self.ui.walletTable.addProxyModel( self.soldOutFilter )

        self.ui.soldOutCB.stateChanged.connect( self._handleSoldOut )

    def connectData(self, dataObject):
        self.dataObject = dataObject
        self.ui.walletTable.connectData( dataObject )
        self.dataObject.stockDataChanged.connect( self.updateView )
        self.dataObject.walletDataChanged.connect( self.updateView )
        self.updateView()

    def updateView(self):
        if self.dataObject is None:
            _LOGGER.warning("unable to update view")
            self.ui.walletTable.clear()
            return
        _LOGGER.info("updating view")
        stock = self.dataObject.getWalletStock()
        if stock is None:
            self.ui.walletTable.clear()
            return
        self.ui.walletTable.setData( stock )

    def importMBTransactions(self):
        self.ui.walletTable.importTransactions()

    def openWalletGainChart(self):
        if self.dataObject is None:
            return
        create_walletgain_window( self.dataObject, self )

    def openWalletProfitChart(self):
        if self.dataObject is None:
            return
        create_wallet_profit_window( self.dataObject, calculateOverall=False, parent=self )

    def openOverallProfitChart(self):
        if self.dataObject is None:
            return
        create_wallet_profit_window( self.dataObject, calculateOverall=True, parent=self )

    def _handleSoldOut(self):
        incluideSoldOut = self.ui.soldOutCB.isChecked()
        self.soldOutFilter.includeSoldOut( incluideSoldOut )


##=============================================================


def import_mb_transactions( dataObject, filePath ):
    importedData, state = load_mb_transactions( filePath )

    print("importing:\n", importedData)

    if state == 0:
        ## load history transactions
        _LOGGER.debug( "opening transactions: %s", filePath )
        dataObject.importWalletTransactions( importedData )
    elif state == 1:
        ## add transactions
        _LOGGER.debug( "opening transactions: %s", filePath )
        dataObject.importWalletTransactions( importedData, True )
    else:
        _LOGGER.warning( "invalid import file: %s", filePath )
