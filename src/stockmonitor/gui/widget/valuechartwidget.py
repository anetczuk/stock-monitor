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
import abc

from PyQt5.QtCore import Qt

from stockmonitor.gui.appwindow import ChartAppWindow
from stockmonitor.gui.utils import set_label_url
from stockmonitor.gui import threadlist
from stockmonitor.gui.widget.mpl.baseintradaychart import set_ref_format_coord

from .. import uiloader

from .mpl.mpltoolbar import NavigationToolbar


_LOGGER = logging.getLogger(__name__)


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class ValueChartBasicWidget(QtBaseClass):                    # type: ignore

#     updateFinished = QtCore.pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        if parentWidget is not None:
            bgcolor = parentWidget.palette().color(parentWidget.backgroundRole())
            self.ui.dataChart.setBackgroundByQColor( bgcolor )

        self.toolbar = NavigationToolbar(self.ui.dataChart, self)
        self.ui.toolbarLayout.addWidget( self.toolbar )

        self.ui.sourceTextLabel.hide()
        self.ui.sourceLabel.hide()
        self.ui.sourceLabel.setOpenExternalLinks(True)

        self.ui.stockLabel.setStyleSheet("font-weight: bold")

        self.ui.refreshPB.clicked.connect( self.refreshData )
        self.ui.rangeCB.currentIndexChanged.connect( self.repaintData )

    def clearData(self):
        self.ui.dataChart.clearPlot()

    def refreshData(self):
        self.updateData( True )

    def repaintData(self):
        self.updateData( False )

    def updateData(self, forceRefresh=False):
        dataSources = self.getDataSources()
        if not dataSources:
            self._updateView()
            return

        if forceRefresh is False:
            for source in dataSources:
                source.getWorksheetData( forceRefresh )
            self._updateView()
            return

        self.ui.refreshPB.setEnabled( False )

#         threads = threadlist.QThreadMeasuredList( self )
        ThreadingListType = threadlist.get_threading_list()
        threads = ThreadingListType( self )
        threads.finished.connect( threads.deleteLater )
        threads.finished.connect( self._updateView, Qt.QueuedConnection )

        for source in dataSources:
            threads.appendFunction( source.getWorksheetData, [forceRefresh] )

        threads.start()

    def _updateView(self):
        rangeText = self.ui.rangeCB.currentText()
        _LOGGER.debug( "updating chart, range[%s]", rangeText )

        self.clearData()

        sourceLink = self.getDataSourceLink()
        if sourceLink is not None:
            self.ui.sourceTextLabel.show()
            self.ui.sourceLabel.show()
            set_label_url( self.ui.sourceLabel, sourceLink )
        else:
            self.ui.sourceTextLabel.hide()
            self.ui.sourceLabel.hide()

        self.ui.refreshPB.setEnabled( True )
        dataFrame = self._getDataFrame()
        if dataFrame is None:
            _LOGGER.warning( "no data received" )
            return

        timeColumn   = dataFrame["t"]
        priceColumn  = dataFrame["c"]

        timeData = list(timeColumn)
        if len(timeData) < 1:
            _LOGGER.warning( "no data received" )
            return

        self.ui.dataChart.addPriceLine( timeData, priceColumn )

        set_ref_format_coord( self.ui.dataChart.pricePlot )
        _LOGGER.debug( "updating chart data done, range[%s]", rangeText )

    @abc.abstractmethod
    def getDataSources(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def getDataSourceLink(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _getDataFrame(self):
        raise NotImplementedError('You need to define this method in derived class!')


# pylint: disable=W0223
class ValueChartWidget( ValueChartBasicWidget ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.dataObject = None
        self.ticker = None

    def connectData(self, dataObject, ticker):
        self.dataObject = dataObject
        self.ticker     = ticker
        self.dataObject.stockDataChanged.connect( self.updateData )
        self.updateData( True )

    def getDataSources(self):
        retList = []
        for i in range(0, self.ui.rangeCB.count()):
            rangeText = self.ui.rangeCB.itemText( i )
            isin = self.dataObject.getStockIsinFromTicker( self.ticker )
            intraSource = self.dataObject.gpwStockIntradayData.getSource( isin, rangeText )
            retList.append( intraSource )
        return retList

    def getDataSourceLink(self):
        intraSource = self.getTickerDataSource()
        return intraSource.sourceLink()

    def getTickerDataSource(self):
        rangeText = self.ui.rangeCB.currentText()
        isin = self.dataObject.getStockIsinFromTicker( self.ticker )
        intraSource = self.dataObject.gpwStockIntradayData.getSource( isin, rangeText )
        return intraSource


class StockValueChartWidget( ValueChartWidget ):

    def _getDataFrame(self):
        rangeText = self.ui.rangeCB.currentText()
        dataFrame = self.dataObject.getWalletStockValueData( self.ticker, rangeText )
        return dataFrame


class StockProfitChartWidget( ValueChartWidget ):

    def _getDataFrame(self):
        rangeText = self.ui.rangeCB.currentText()
        dataFrame = self.dataObject.getWalletStockProfitData( self.ticker, rangeText )
        return dataFrame


class WalletProfitChartWidget( ValueChartBasicWidget ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.dataObject = None

    def connectData(self, dataObject):
        self.dataObject = dataObject
        self.dataObject.stockDataChanged.connect( self.updateData )
        self.updateData( True )

    def getDataSources(self):
        retList = []
        rangeText = self.ui.rangeCB.currentText()
        walletTickers = self.dataObject.wallet.tickers()
        for ticker in walletTickers:
            isin = self.dataObject.getStockIsinFromTicker( ticker )
            intraSource = self.dataObject.gpwStockIntradayData.getSource( isin, rangeText )
            retList.append( intraSource )
        return retList

#         retList = []
#         walletTickers = self.dataObject.wallet.tickers()
#         for ticker in walletTickers:
#             isin = self.dataObject.getStockIsinFromTicker( ticker )
#             for i in range(0, self.ui.rangeCB.count()):
#                 rangeText = self.ui.rangeCB.itemText( i )
#                 intraSource = self.dataObject.gpwStockIntradayData.getSource( isin, rangeText )
#                 retList.append( intraSource )
#         return retList

    def getDataSourceLink(self):
        return None

    def _getDataFrame(self):
        rangeText = self.ui.rangeCB.currentText()
        dataFrame = self.dataObject.getWalletOverallProfitData( rangeText )
        return dataFrame


class WalletGainChartWidget( ValueChartBasicWidget ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.dataObject = None

        cSize = self.ui.rangeCB.count()
        if cSize > 0:
            self.ui.rangeCB.setCurrentIndex( cSize - 1 )

    def connectData(self, dataObject):
        self.dataObject = dataObject
        self.dataObject.walletDataChanged.connect( self.updateData )
        self.updateData( True )

    def getDataSources(self):
        ## nothing to update -- gain is not affected by current values of stock
        return []

#         retList = []
#         rangeText = self.ui.rangeCB.currentText()
#         walletTickers = self.dataObject.wallet.tickers()
#         for ticker in walletTickers:
#             isin = self.dataObject.getStockIsinFromTicker( ticker )
#             intraSource = self.dataObject.gpwStockIntradayData.getSource( isin, rangeText )
#             retList.append( intraSource )
#         return retList

#         retList = []
#         walletTickers = self.dataObject.wallet.tickers()
#         for ticker in walletTickers:
#             isin = self.dataObject.getStockIsinFromTicker( ticker )
#             for i in range(0, self.ui.rangeCB.count()):
#                 rangeText = self.ui.rangeCB.itemText( i )
#                 intraSource = self.dataObject.gpwStockIntradayData.getSource( isin, rangeText )
#                 retList.append( intraSource )
#         return retList

    def getDataSourceLink(self):
        return None

    def _getDataFrame(self):
        if self.dataObject is None:
            return None
        rangeText = self.ui.rangeCB.currentText()
        dataFrame = self.dataObject.getWalletGainData( rangeText )
        return dataFrame


## ==================================================================================


def create_window( dataObject, ticker, chartWidgetClass, parent=None ):
    chartWindow = ChartAppWindow( parent )
    chart = chartWidgetClass( chartWindow )
    chartWindow.addWidget( chart )
    chartWindow.refreshAction.triggered.connect( chart.refreshData )

    chart.connectData(dataObject, ticker)

    name = dataObject.getNameFromTicker( ticker )
    if name is not None:
        title = name + " [" + ticker + "]"
        chartWindow.setWindowTitleSuffix( "- " + title )
        chart.ui.stockLabel.setText( name )

    chartWindow.show()

    return chartWindow


def create_stockvalue_window( dataObject, ticker, parent=None ):
    return create_window(dataObject, ticker, StockValueChartWidget, parent)


def create_stockprofit_window( dataObject, ticker, parent=None ):
    return create_window(dataObject, ticker, StockProfitChartWidget, parent)


def create_walletprofit_window( dataObject, parent=None ):
    chartWindow = ChartAppWindow( parent )
    chart = WalletProfitChartWidget( chartWindow )
    chartWindow.addWidget( chart )
    chartWindow.refreshAction.triggered.connect( chart.refreshData )

    chart.connectData(dataObject)

    title = "Wallet"
    chartWindow.setWindowTitleSuffix( "- " + title )
    chart.ui.stockLabel.setText( title )

    chartWindow.show()

    return chartWindow


def create_walletgain_window( dataObject, parent=None ):
    chartWindow = ChartAppWindow( parent )
    chart = WalletGainChartWidget( chartWindow )
    chartWindow.addWidget( chart )
    chartWindow.refreshAction.triggered.connect( chart.refreshData )

    chart.connectData(dataObject)

    title = "Wallet"
    chartWindow.setWindowTitleSuffix( "- " + title )
    chart.ui.stockLabel.setText( title )

    chartWindow.show()

    return chartWindow
