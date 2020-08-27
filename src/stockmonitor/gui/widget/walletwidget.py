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

import pandas

from PyQt5.QtWidgets import QMenu, QFileDialog
from PyQt5.QtGui import QCursor

from .. import uiloader

from .stocktable import StockTable


_LOGGER = logging.getLogger(__name__)


class WalletStockTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("walletstocktable")

    def contextMenuEvent( self, _ ):
        contextMenu         = QMenu(self)
        if self.dataObject is not None:
            stockInfoAction     = contextMenu.addAction("Stock info")
            importTransAction   = contextMenu.addAction("Import mb transactions")
            stockInfoAction.triggered.connect( self._openInfo )
            importTransAction.triggered.connect( self._importTransactions )
        self._addFavActions( contextMenu )
        contextMenu.addSeparator()
        filterDataAction    = contextMenu.addAction("Filter data")
        configColumnsAction = contextMenu.addAction("Configure columns")

        filterDataAction.triggered.connect( self.showFilterConfiguration )
        configColumnsAction.triggered.connect( self.showColumnsConfiguration )

        if self._rawData is None:
            configColumnsAction.setEnabled( False )

        globalPos = QCursor.pos()
        contextMenu.exec_( globalPos )

    def _importTransactions(self):
        if self.dataObject is None:
            return
        filePath = QFileDialog.getOpenFileName( self,
                                                "Import transactions" )
        if not filePath:
            return
        dataPath = filePath[0]
        importedData = import_mb_transactions( dataPath )
#         print("data:\n", importedData)
        self.dataObject.importWalletTransactions( importedData )

    def _getSelectedCodes(self):
        dataAccess = self.dataObject.gpwCurrentData
        selectedRows = self.getSelectedRows()
        favCodes = set()
        for dataRow in selectedRows:
            stockName = self._rawData.iloc[dataRow, 0]
            code = dataAccess.getShortFieldByName( stockName )
            if code is not None:
                favCodes.add( code )
        favList = list(favCodes)
        return favList


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class WalletWidget( QtBaseClass ):           # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.dataObject = None

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


def import_mb_transactions( dataPath ):
    _LOGGER.debug( "opening transactions: %s", dataPath )
    dataFrame = pandas.read_csv( dataPath, names=["trans_time", "name", "stock_id", "k_s", "amount",
                                                  "unit_price", "unit_currency", "price", "currency"],
                                 sep=';', decimal=',', thousands=' ' )
    return dataFrame
