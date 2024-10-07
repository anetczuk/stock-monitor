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

from pandas.core.frame import DataFrame

from stockmonitor.gui.dataobject import DataObject
from stockmonitor.gui.appwindow import AppWindow

from .. import uiloader


_LOGGER = logging.getLogger(__name__)


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class StockSummaryWidget(QtBaseClass):                    # type: ignore

#     updateFinished = QtCore.pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.dataObject: DataObject = None
        self.isin = None

    def connectData(self, dataObject, isin):
        self.isin       = isin
        self.dataObject = dataObject
        self.ui.espiList.connectData( dataObject )
        self.ui.reportswidget.connectData( dataObject )
        self.ui.reportswidget.dataTable.filteringEnabled = False
        self.dataObject.stockDataChanged.connect( self.updateView )
        self.dataObject.walletDataChanged.connect( self.updateView )
        self.updateView()

    def updateView(self):
        self.ui.espiList.clear()
        if self.dataObject is None:
            _LOGGER.warning("unable to update view")
            return
        espiData = self.dataObject.gpwESPIData
        if espiData is None:
            _LOGGER.info("no data to view")
            return
        dataFrame: DataFrame = espiData.getWorksheetData()
        if dataFrame is not None:
            dataFrame = dataFrame[ dataFrame['isin'] == self.isin ]
        self.ui.espiList.setData( dataFrame )

        self.ui.reportswidget.refreshData()
        stock_ticker = self.dataObject.getTickerFromIsin( self.isin )
        self.ui.reportswidget.dataTable.setDataFilter(1, 1, stock_ticker)


def create_window( dataObject, isin, parent=None ):
    newWindow = AppWindow( parent )
    summary = StockSummaryWidget( newWindow )
    newWindow.addWidget( summary )
    newWindow.refreshAction.triggered.connect( summary.updateView )

    summary.connectData(dataObject, isin)

    name = dataObject.getNameFromIsin( isin )
    if name is not None:
        title = name + " [" + isin + "]"
        newWindow.setWindowTitleSuffix( "- " + title )
        summary.ui.stockLabel.setText( name )

    newWindow.show()

    return newWindow
