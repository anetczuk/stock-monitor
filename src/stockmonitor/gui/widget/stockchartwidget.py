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

from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, QtGui

from stockmonitor.gui.dataobject import WalletData
from stockmonitor.gui.appwindow import AppWindow
from stockmonitor.gui.utils import set_label_url
from stockmonitor.gui import threadlist
from stockmonitor.gui.widget.mpl.baseintradaychart import set_ref_format_coord,\
    set_int_format_coord

from .. import uiloader

from .mpl.mpltoolbar import NavigationToolbar


_LOGGER = logging.getLogger(__name__)


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class StockChartWidget(QtBaseClass):                    # type: ignore

#     updateFinished = QtCore.pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.dataObject = None
        self.ticker = None

        if parentWidget is not None:
            bgcolor = parentWidget.palette().color(parentWidget.backgroundRole())
            self.ui.dataChart.setBackgroundByQColor( bgcolor )

        self.toolbar = NavigationToolbar(self.ui.dataChart, self)
        self.ui.toolbarLayout.addWidget( self.toolbar )

        self.ui.sourceLabel.setOpenExternalLinks(True)

        self.ui.stockLabel.setStyleSheet("font-weight: bold")

        self.ui.showWalletCB.setChecked( False )
        self.ui.showTransactionsCB.setChecked( False )
        self.ui.showWalletCB.stateChanged.connect( self.repaintData )
        self.ui.showTransactionsCB.stateChanged.connect( self.repaintData )

        self.ui.refreshPB.clicked.connect( self.refreshData )
        self.ui.rangeCB.currentIndexChanged.connect( self.repaintData )

    def connectData(self, dataObject, ticker):
        self.dataObject = dataObject
        self.ticker     = ticker
        self.dataObject.stockDataChanged.connect( self.updateData )
        self.updateData( True )

    def clearData(self):
        self.ui.dataChart.clearPlot()

    def refreshData(self):
        self.updateData( True )

    def repaintData(self):
        self.updateData( False )

    def updateData(self, forceRefresh):
        self.ui.refreshPB.setEnabled( False )

        threads = threadlist.QThreadMeasuredList( self )
        threads.finished.connect( threads.deleteLater )
        threads.finished.connect( self._updateView, Qt.QueuedConnection )

        intraSource = self.getIntradayDataSource()
        threads.appendFunction( intraSource.getWorksheet, [forceRefresh] )

        currentData = self.getCurrentDataSource()
        threads.appendFunction( currentData.loadWorksheet, [forceRefresh] )

        threads.start()

#         intraSource = self.getIntradayDataSource()
#         intraSource.getWorksheet( forceRefresh )
#         currentData = self.getCurrentDataSource()
#         currentData.loadWorksheet( forceRefresh )
#         self._updateView()

    def _updateView(self):
        self.ui.refreshPB.setEnabled( True )

        rangeText = self.ui.rangeCB.currentText()
        isin = self.dataObject.getStockIsinFromTicker( self.ticker )
        _LOGGER.debug( "updating chart data, range[%s] isin[%s]", rangeText, isin )

        intraSource = self.getIntradayDataSource()
        dataFrame = intraSource.getWorksheet()

        self.clearData()
        if dataFrame is None:
            return

        currentData = self.getCurrentDataSource()
        currentData.loadWorksheet()

        timeColumn   = dataFrame["t"]
        priceColumn  = dataFrame["c"]
        volumeColumn = dataFrame["v"]
#         print( "got intraday data:", priceColumn )

        price     = currentData.getRecentValue( self.ticker )
        change    = currentData.getRecentChange( self.ticker )
        volumen   = volumeColumn.iloc[-1]
        refPrice  = currentData.getReferenceValue( self.ticker )
        timestamp = timeColumn.iloc[-1]

        timeData = list(timeColumn)
        self.ui.dataChart.addPriceLine( timeData, priceColumn )

        self.ui.dataChart.addPriceSecondaryY( refPrice )

        refX = [ timeData[0], timeData[-1] ]
        refY = [ refPrice, refPrice ]
        self.ui.dataChart.addPriceLine( refX, refY, style="--" )

        walletStock: WalletData = self.dataObject.wallet[ self.ticker ]
        if walletStock is not None:
            if self.ui.showWalletCB.isChecked():
                amount, buy_unit_price = walletStock.currentTransactionsAvg()
                if amount > 0:
                    refY = [ buy_unit_price, buy_unit_price ]
                    self.ui.dataChart.addPriceLine( refX, refY, color='black', style="--" )

            if self.ui.showTransactionsCB.isChecked():
                currTransactions = walletStock.currentTransactions()
                for item in currTransactions:
                    amount         = item[0]
                    buy_unit_price = item[1]
                    refY = [ buy_unit_price, buy_unit_price ]
                    self.ui.dataChart.addPriceLine( refX, refY, color='blue', style="--" )

        self.ui.dataChart.addVolumeLine( timeData, volumeColumn )

        set_ref_format_coord( self.ui.dataChart.pricePlot, refPrice )
        set_int_format_coord( self.ui.dataChart.volumePlot )

        self.ui.valueLabel.setText( str(price) )
        self.ui.changeLabel.setText( str(change) + "%" )
        self.ui.volumeLabel.setText( str(volumen) )
        self.ui.timeLabel.setText( str(timestamp) )

        set_label_url( self.ui.sourceLabel, intraSource.sourceLink() )

    def getIntradayDataSource(self):
        rangeText = self.ui.rangeCB.currentText()
        isin = self.dataObject.getStockIsinFromTicker( self.ticker )
        intraSource = self.dataObject.gpwStockIntradayData.getSource( isin, rangeText )
        return intraSource

    def getCurrentDataSource(self):
        return self.dataObject.gpwCurrentData


class StockChartWindow( AppWindow ):

    def __init__(self, parentWidget=None):
        super().__init__( parentWidget )

        self.chart = StockChartWidget( self )
        self.addWidget( self.chart )

        self.refreshAction = QtWidgets.QAction(self)
        self.refreshAction.setShortcuts( QtGui.QKeySequence.Refresh )
        self.refreshAction.triggered.connect( self.chart.refreshData )
        self.addAction( self.refreshAction )

    def connectData(self, dataObject, ticker):
        self.chart.connectData(dataObject, ticker)
        self._setStockName()

    def _setStockName(self):
        name = self.chart.dataObject.getNameFromTicker( self.chart.ticker )
        if name is None:
            return
        title = name + " [" + self.chart.ticker + "]"
        self.setWindowTitleSuffix( "- " + title )
        self.chart.ui.stockLabel.setText( name )
