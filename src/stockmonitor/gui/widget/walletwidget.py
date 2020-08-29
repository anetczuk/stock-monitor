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

from PyQt5 import QtCore
from PyQt5.QtWidgets import QMenu, QFileDialog
from PyQt5.QtGui import QCursor

from stockmonitor.dataaccess.convert import convert_float, convert_int

from .. import uiloader

from .stocktable import StockTable
from stockmonitor.gui.widget.stocktable import insert_new_action


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


## =================================================================


class WalletStockTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("walletstocktable")

    def createContextMenu(self):
        contextMenu = super().createContextMenu()
        if self.dataObject is not None:
            importTransAction = insert_new_action(contextMenu, "Import mb transactions", 1)
            importTransAction.triggered.connect( self._importTransactions )
        return contextMenu

    def _importTransactions(self):
        if self.dataObject is None:
            return
        filePath = QFileDialog.getOpenFileName( self, "Import transactions" )
        if not filePath:
            return
        dataPath = filePath[0]
        if not dataPath:
            return
        importedData = import_mb_transactions( dataPath )
#         importedData = import_mb_orders( dataPath )
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

    def _handleSoldOut(self):
        incluideSoldOut = self.ui.soldOutCB.isChecked()
        self.soldOutFilter.includeSoldOut( incluideSoldOut )


def import_mb_transactions( dataPath ):
    ## imported transaction values are not affected by borker's commission
    ## real sell profit is transaction value decreased by broker's commission
    ## real buy cost is transaction value increased by broker's commission
    ## broker commission: greater of 3PLN and 0.39%

    _LOGGER.debug( "opening transactions: %s", dataPath )
    dataFrame = pandas.read_csv( dataPath, names=["trans_time", "name", "stock_id", "k_s", "amount",
                                                  "unit_price", "unit_currency", "price", "currency"],
                                 sep=';', decimal=',', thousands=' ' )

    #### fix names to match GPW names
    ## XTRADEBDM -> XTB
    ## CELONPHARMA -> CLNPHARMA
    dataFrame["name"].replace({"XTRADEBDM": "XTB", "CELONPHARMA": "CLNPHARMA"}, inplace=True)

    dataFrame['amount'] = dataFrame['amount'].apply( convert_int )

    dataFrame['unit_price'] = dataFrame['unit_price'].apply( convert_float )
    dataFrame['price'] = dataFrame['price'].apply( convert_float )

    return dataFrame
