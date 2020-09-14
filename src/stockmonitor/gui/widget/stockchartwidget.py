# MIT License
#
# Copyright (c) 2017 Arkadiusz Netczuk <dev.arnet@gmail.com>
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

from stockmonitor.gui.appwindow import AppWindow

from .. import uiloader

from .mpl.mpltoolbar import DynamicToolbar


_LOGGER = logging.getLogger(__name__)


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class StockChartWidget(QtBaseClass):                    # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.dataObject = None
        self.ticker = None

        if parentWidget is not None:
            bgcolor = parentWidget.palette().color(parentWidget.backgroundRole())
            self.ui.dataChart.setBackgroundByQColor( bgcolor )

        self.toolbar = DynamicToolbar(self.ui.dataChart, self)
        self.ui.toolbarLayout.addWidget( self.toolbar )

        self.ui.sourceLabel.setOpenExternalLinks(True)

        self.ui.stockLabel.setStyleSheet("font-weight: bold")

        self.ui.showWalletCB.setChecked( False )
        self.ui.showTransactionsCB.setChecked( False )
        self.ui.showWalletCB.stateChanged.connect( self.updateData )
        self.ui.showTransactionsCB.stateChanged.connect( self.updateData )
        
        self.ui.refreshPB.clicked.connect( self.refreshData )

    def connectData(self, dataObject, ticker):
        self.dataObject = dataObject
        self.ticker     = ticker
        self.dataObject.stockDataChanged.connect( self.updateData )
        self.updateData()

    def clearData(self):
        self.ui.dataChart.clearLines()

    def refreshData(self):
        self.updateData( True )

    def updateData(self, forceRefresh=False):
        isin = self.dataObject.getStockIsinFromTicker( self.ticker )
        intraSource = self.dataObject.gpwStockIntradayData.getSource( isin )
        dataFrame = intraSource.getWorksheet( forceRefresh )

        self.clearData()
        if dataFrame is None:
            return

        timeColumn   = dataFrame["t"]
        priceColumn  = dataFrame["c"]
        volumeColumn = dataFrame["v"]
#         print( "got intraday data:", priceColumn )

        currentData = self.dataObject.gpwCurrentData
        currentData.loadWorksheet( forceRefresh )

        price     = currentData.getRecentValue( self.ticker )
        change    = currentData.getRecentChange( self.ticker )
        volumen   = volumeColumn.iloc[-1]
        refPrice  = currentData.getReferenceValue( self.ticker )
        timestamp = timeColumn.iloc[-1]

        timeData = list(timeColumn)
        self.addPriceLine( timeData, priceColumn )

        refX = [ timeData[0], timeData[-1] ]
        refY = [ refPrice, refPrice ]
        self.addPriceLine( refX, refY, style="--" )

        walletStock = self.dataObject.wallet[ self.ticker ]
        if walletStock is not None:
            if self.ui.showWalletCB.isChecked():
                amount, buy_unit_price = walletStock.calc2()
                if amount > 0:
                    refY = [ buy_unit_price, buy_unit_price ]
                    self.addPriceLine( refX, refY, color='black', style="--" )

            if self.ui.showTransactionsCB.isChecked():
                currTransactions = walletStock.currentTransactions()
                for item in currTransactions:
                    amount         = item[0]
                    buy_unit_price = item[1]
                    refY = [ buy_unit_price, buy_unit_price ]
                    self.addPriceLine( refX, refY, color='blue', style="--" )

        self.addVolumeLine( timeData, volumeColumn )

        self.ui.valueLabel.setText( str(price) )
        self.ui.changeLabel.setText( str(change) + "%" )
        self.ui.volumeLabel.setText( str(volumen) )
        self.ui.timeLabel.setText( str(timestamp) )

        sourceUrl = intraSource.sourceLink()
        htmlText = "<a href=\"%s\">%s</a>" % (sourceUrl, sourceUrl)
        self.ui.sourceLabel.setText( htmlText )

#     def loadSettings(self, settings):
#         settings.beginGroup( self.objectName() )
#         enabled = settings.value("chart_enabled", True, type=bool)
#         settings.endGroup()
#
#         self.ui.enabledCB.setChecked( enabled )
#
#     def saveSettings(self, settings):
#         settings.beginGroup( self.objectName() )
#         enabledChart = self.ui.enabledCB.isChecked()
#         settings.setValue("chart_enabled", enabledChart)
#         settings.endGroup()

    def addPriceLine(self, xdata, ydata, color='r', style=None ):
        self.ui.dataChart.addPriceLine( xdata, ydata, color, style )
        self.ui.dataChart.draw_idle()

    def addVolumeLine(self, xdata, ydata, color='b', style=None ):
        self.ui.dataChart.addVolumeLine( xdata, ydata, color, style )
        self.ui.dataChart.draw_idle()


class StockChartWindow( AppWindow ):

    def __init__(self, parentWidget=None):
        super().__init__( parentWidget )

        self.chart = StockChartWidget( self )
        self.addWidget( self.chart )

    def connectData(self, dataObject, ticker):
        self.chart.connectData(dataObject, ticker)
        self._setStockName()

    def updateData(self):
        self.chart.updateData()

    def _setStockName(self):
        name = self.chart.dataObject.getNameFromTicker( self.chart.ticker )
        if name is None:
            return
        title = name + " [" + self.chart.ticker + "]"
        self.setWindowTitleSuffix( "- " + title )
        self.chart.ui.stockLabel.setText( name )
