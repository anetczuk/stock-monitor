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

from .. import uiloader

from .stocktable import StockTable


_LOGGER = logging.getLogger(__name__)


class TransactionsTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("transactionstable")

    def _getSelectedTickers(self):
        return self.getSelectedData( 1 )                ## ticker


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class TransactionsWidget( QtBaseClass ):           # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.dataObject = None

        self.ui.reduceToCurrentCB.stateChanged.connect( self.updateView )

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
        showCurrent = self.ui.reduceToCurrentCB.isChecked()
        if showCurrent:
            transactions = self.dataObject.getWalletTransactions()
        else:
            transactions = self.dataObject.getAllTransactions()
        if transactions is None:
            self.ui.transactionsTable.clear()
            return
        self.ui.transactionsTable.setData( transactions )
