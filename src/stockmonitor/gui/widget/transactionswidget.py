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

from PyQt5 import QtGui
from PyQt5.QtCore import QModelIndex

from stockmonitor.gui.dataobject import DataObject

from .. import uiloader

from .stocktable import StockTable, TableRowColorDelegate


_LOGGER = logging.getLogger(__name__)


class TransactionsColorDelegate( TableRowColorDelegate ):

    def __init__(self, dataObject: DataObject):
        super().__init__()
        self.dataObject = dataObject

    ## override
    def foreground(self, index: QModelIndex ):
        dataColumn = index.column()
        ## "Zysk %"
        if dataColumn == 6:
            stockChangeString = index.data()
            if stockChangeString != "-":
                stockChange = float(stockChangeString)
                if stockChange > 0.0:
                    return QtGui.QColor( "green" )
    #             return QtGui.QColor( "red" )
        return None

#     ## override
#     def background(self, index: QModelIndex ):
#         sourceParent = index.parent()
#         dataRow = index.row()
#         dataIndex = self.parent.index( dataRow, 3, sourceParent )       ## get ticker
#         ticker = dataIndex.data()
#         markerColor = marker_background_color( self.dataObject, ticker )
#         if markerColor is not None:
#             return markerColor
#         return wallet_background_color( self.dataObject, ticker )


class TransactionsTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("transactionstable")

    def connectData(self, dataObject):
        super().connectData( dataObject )
        colorDecorator = TransactionsColorDelegate( self.dataObject )
        self.setColorDelegate( colorDecorator )

    def _getSelectedTickers(self):
        return self.getSelectedData( 1 )                ## ticker


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class TransactionsWidget( QtBaseClass ):           # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.dataObject = None

        self.ui.transactionsScopeCB.currentIndexChanged.connect( self.updateView )

    def connectData(self, dataObject):
        self.dataObject = dataObject
        self.ui.transactionsTable.connectData( dataObject )
        self.dataObject.stockDataChanged.connect( self.updateView )
        self.dataObject.walletDataChanged.connect( self.updateView )
        self.updateView()

    def updateView(self):
        if self.dataObject is None:
            _LOGGER.warning("unable to update view")
            self.ui.walletTable.clear()
            return
        _LOGGER.info("updating view")
        transactions = None
        currIndex = self.ui.transactionsScopeCB.currentIndex()
        if currIndex == 0:
            transactions = self.dataObject.getWalletBuyTransactions()
        elif currIndex == 1:
            transactions = self.dataObject.getWalletSellTransactions()
        elif currIndex == 2:
            transactions = self.dataObject.getAllTransactions()
        if transactions is None:
            self.ui.transactionsTable.clear()
            return
        self.ui.transactionsTable.setData( transactions )
