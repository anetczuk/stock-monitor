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
import tempfile
import codecs

import pandas

from PyQt5 import QtCore
from PyQt5.QtWidgets import QFileDialog

from stockmonitor.dataaccess.convert import convert_float, convert_int
from stockmonitor.dataaccess.gpwdata import apply_on_column

from .. import uiloader

from .stocktable import StockTable


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

#     def createContextMenu(self):
#         contextMenu = super().createContextMenu()
#         if self.dataObject is not None:
#             importTransAction = insert_new_action(contextMenu, "Import mb transactions", 1)
#             importTransAction.triggered.connect( self.importTransactions )
#         return contextMenu

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
        return self.getSelectedData( 1 )                ## ticker


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class WalletWidget( QtBaseClass ):           # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.dataObject = None

        self.soldOutFilter = WalletProxyModel()
        self.ui.walletTable.addProxyModel( self.soldOutFilter )

        self.ui.walletProfitLabel.setStyleSheet("font-weight: bold")
        self.ui.overallProfitLabel.setStyleSheet("font-weight: bold")

        self.ui.importMBPB.clicked.connect( self.ui.walletTable.importTransactions )

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

        profit = self.dataObject.getWalletProfit()
        walletProfit = profit[0]
        overallProfit = profit[1]
        self.ui.walletProfitLabel.setText( str(walletProfit) )
        self.ui.overallProfitLabel.setText( str(overallProfit) )

    def _handleSoldOut(self):
        incluideSoldOut = self.ui.soldOutCB.isChecked()
        self.soldOutFilter.includeSoldOut( incluideSoldOut )


def import_mb_transactions( dataObject, filePath ):
    ## imported transaction values are not affected by borker's commission
    ## real sell profit is transaction value decreased by broker's commission
    ## real buy cost is transaction value increased by broker's commission
    ## broker commission: greater of 5PLN and 0.39%

    ##
    ## find line in file and remove header information leaving raw data
    ##
    tmpfile = tempfile.NamedTemporaryFile( mode='w+t' )
    headerFound = False
    historyFound = False
    currentFound = False

    with codecs.open(filePath, 'r', encoding='utf-8', errors='replace') as srcFile:
        for line in srcFile:
            if headerFound:
                tmpfile.write(line)
            elif "Czas transakcji" in line:
                headerFound = True
            elif "Historia transakcji" in line:
                historyFound = True
            elif "Transakcje bie" in line:
                currentFound = True
    tmpfile.seek(0)

    sourceFile = None
    if headerFound:
        sourceFile = tmpfile
    else:
        sourceFile = filePath

    if historyFound:
        ## load history transactions
        _LOGGER.debug( "opening transactions: %s", filePath )
        importedData = load_mb_transactions( sourceFile )
        dataObject.importWalletTransactions( importedData )
        tmpfile.close()
    elif currentFound:
        ## add transactions
        _LOGGER.debug( "opening transactions: %s", filePath )
        importedData = load_mb_transactions( sourceFile )
        dataObject.importWalletTransactions( importedData, True )
        tmpfile.close()
    else:
        _LOGGER.warning( "invalid import file: %s", filePath )


def load_mb_transactions( sourceFile ):
    dataFrame = pandas.read_csv( sourceFile, names=["trans_time", "name", "stock_id", "k_s", "amount",
                                                    "unit_price", "unit_currency", "price", "currency"],
                                 sep=r'[;\t]', decimal=',', thousands=' ', engine='python', encoding='utf_8' )

#     print( "raw data:\n", dataFrame )

    apply_on_column( dataFrame, 'name', str )

    #### fix names to match GPW names
    ## XTRADEBDM -> XTB
    ## CELONPHARMA -> CLNPHARMA
    dataFrame["name"].replace({"XTRADEBDM": "XTB", "CELONPHARMA": "CLNPHARMA"}, inplace=True)

    apply_on_column( dataFrame, 'amount', convert_int )

    apply_on_column( dataFrame, 'unit_price', convert_float )
    apply_on_column( dataFrame, 'price', convert_float )

    return dataFrame
