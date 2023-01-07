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

from typing import Dict, List

import pandas

from PyQt5.QtCore import Qt
# from PyQt5.QtGui import QCloseEvent

from stockdataaccess.dataaccess.gpw.gpwcurrentdata import GpwCurrentStockData
from stockdataaccess.dataaccess.gpw.gpwintradaydata import GpwCurrentStockIntradayData
from stockmonitor.datatypes.stocktypes import GpwStockIntradayMap
from stockmonitor.datatypes.wallettypes import TransHistory
from stockmonitor.gui import threadlist
from stockmonitor.gui.dataobject import DataObject
from stockmonitor.gui.appwindow import ChartAppWindow
from stockmonitor.gui.utils import set_label_url
from stockmonitor.gui.widget.mpl import mplbasechart
from stockmonitor.gui.widget.mpl import candlestickchart

from .. import uiloader

from .mpl.mpltoolbar import NavigationToolbar
from stockmonitor.gui.widget.stockchartwidget import prepare_candle_data
import matplotlib.pyplot


_LOGGER = logging.getLogger(__name__)


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class StockMosaicWidget(QtBaseClass):                    # type: ignore
    ## double, price and volumen chart

#     updateFinished = QtCore.pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.dataObject: DataObject = None
        self.tickerList = None
        self._currBinsNum = 100
        self._updateTimerId = 0

        if parentWidget is not None:
            bgcolor = parentWidget.palette().color(parentWidget.backgroundRole())
            self.ui.candleChart.setBackgroundByQColor( bgcolor )

        self.toolbar = NavigationToolbar(self.ui.candleChart, self)
        self.ui.toolbarLayout.addWidget( self.toolbar )
        self.ui.candleChart.show()

        self.ui.stockLabel.setStyleSheet("font-weight: bold")

        self.ui.showWalletCB.setChecked( False )
        self.ui.showWalletCB.stateChanged.connect( self.repaintData )
        self.ui.showTransactionsLevelsCB.setChecked( False )
        self.ui.showTransactionsLevelsCB.stateChanged.connect( self.repaintData )
        self.ui.showTransactionsPointsCB.setChecked( True )
        self.ui.showTransactionsPointsCB.stateChanged.connect( self.repaintData )

        self.ui.refreshPB.clicked.connect( self.refreshData )
        self.ui.rangeCB.currentIndexChanged.connect( self.repaintData )
        self.ui.sortPlotsCB.currentIndexChanged.connect( self._sortPlotsChanged )

    def connectData(self, dataObject: DataObject, tickerList):
        self.dataObject = dataObject
        self.tickerList = list( tickerList )
        self.dataObject.stockDataChanged.connect( self.updateData )

        tickerSize = len( self.tickerList )
        self.ui.candleChart.generateMosaicItems( tickerSize, hspace=0.04 )

        self.tickerList = zip( self.tickerList, self.tickerList, [0.0] * len(self.tickerList) )
        self.tickerList = list( self.tickerList )
        self._refreshTickersList()
        self._sortPlots( False )
#         self.updateData( False )

        for tickerIndex in range( 0, tickerSize ):
            pricePlot  = self.ui.candleChart.getPricePlot( tickerIndex )
            volumePlot = self.ui.candleChart.getVolumePlot( tickerIndex )
            clear_labels( pricePlot )
            clear_labels( volumePlot )

    def clearData(self):
        self.ui.candleChart.clearPlot()

    def refreshData(self):
        self.updateData( True )

    def repaintData(self):
        self.updateData( False )

    ## 'access' means "download data if None"
    def updateData(self, forceRefresh=False, access=False):
        if self.dataObject is None:
            return

        dataSources = self._dataSourceObjectsList()
        if not dataSources:
            self._updateView()
            return

        if forceRefresh is False and access is False:
            for source in dataSources:
                source.getWorksheetData( forceRefresh )
            self._updateView()
            return

        self.ui.refreshPB.setEnabled( False )

        ThreadingListType = threadlist.get_threading_list_class()
        threads = ThreadingListType( self )
        threads.finished.connect( self._sortPlots )
        threads.deleteOnFinish()

        for source in dataSources:
            if access is False:
                threads.appendFunction( source.getWorksheetData, [forceRefresh] )
            else:
                threads.appendFunction( source.accessWorksheetData, [forceRefresh] )

        threads.start()

    def _sortPlotsChanged(self):
        self._sortPlots( True )

    def _sortPlots(self, update_view=True):
        sortIndex = self.ui.sortPlotsCB.currentIndex()
        if sortIndex == 0:
            ## sort by name
            self.tickerList = sorted( self.tickerList, key=lambda x: x[1] )
            if update_view:
                self._updateView()
            ##self.repaintData()
            return
        if sortIndex == 1:
            ## sort by change
            self._refreshTickersList()
            self.tickerList = sorted( self.tickerList, key=lambda x: x[2] )
            self.tickerList.reverse()
            if update_view:
                self._updateView()
            ##self.repaintData()
            return

        sortText = self.ui.sortPlotsCB.currentText()
        _LOGGER.warning( "unhandled sort value -- %s: %s", sortIndex, sortText )

    # pylint: disable=R0914
    def _updateView(self):
        self.ui.refreshPB.setEnabled( True )

        rangeText = self.ui.rangeCB.currentText()

        currentSource: GpwCurrentStockData = self.getCurrentDataSource()
        currentSource.getWorksheetData()

        self.clearData()

        minTransTime = None
        maxTransTime = None

        tickerSize = len( self.tickerList )
        for index in range( 0, tickerSize ):
            ticker_pair = self.tickerList[ index ]
            ticker = ticker_pair[0]
            isin = self.dataObject.getStockIsinFromTicker( ticker )

            intraSource: GpwCurrentStockIntradayData = self.getIntradayDataSource( ticker )

            transTime = intraSource.getRecentTransTime()
            if transTime is not None:
                if maxTransTime is None or transTime > maxTransTime:
                    maxTransTime = transTime

            dataFrame = intraSource.getWorksheetData()
            if dataFrame is not None:
                startTime = dataFrame.iloc[ 0 ].at[ 't' ]
                if minTransTime is None or startTime < minTransTime:
                    minTransTime = startTime

        self.ui.timeLabel.setText( str(maxTransTime) )

        for index in range( 0, tickerSize ):
            ticker_pair = self.tickerList[ index ]
            ticker = ticker_pair[0]
            isin = self.dataObject.getStockIsinFromTicker( ticker )
            _LOGGER.debug( "updating chart data, range[%s] isin[%s] index[%s]", rangeText, isin, index )

            intraSource: GpwCurrentStockIntradayData = self.getIntradayDataSource( ticker )
            self._updateCandleChart( intraSource, index, minTransTime, maxTransTime )

        self.ui.candleChart.refreshCanvas()

    def _updateCandleChart( self, intraSource: GpwCurrentStockIntradayData, tickerIndex, minTransTime, maxTransTime ):
        ## get data
        ##intraSource = self.dataObject.gpwStockIntradayData.getSource( isin, rangeText )
        ##return intraSource

        ticker_pair = self.tickerList[ tickerIndex ]
        ticker       = ticker_pair[0]
        name         = ticker_pair[1]
        recentChange = ticker_pair[2]

        pricePlot  = self.ui.candleChart.getPricePlot( tickerIndex )
        volumePlot = self.ui.candleChart.getVolumePlot( tickerIndex )

        currentSource: GpwCurrentStockData = self.getCurrentDataSource()

        if isinstance(recentChange, float):
            if recentChange > 0.0:
                recentChange = "+" + str(recentChange)
            title = f"{name} ({ticker})   {recentChange}%"
        else:
            title = f"{name} ({ticker})   {recentChange}"

        candleFrame = prepare_candle_data( intraSource, self._currBinsNum )
        if candleFrame is None or len( candleFrame ) < 2:
            ## no data to show
            pricePlot.set_title( title )
            clear_labels( pricePlot )
            clear_labels( volumePlot )
            return

#         print( ticker, tickerIndex, "\n", candleFrame )

#         dataFrame = intraSource.getWorksheetData()

        timeColumn   = candleFrame.index
        priceColumn  = candleFrame["Close"]

        refPrice    = currentSource.getReferenceValueByTicker( ticker )

        self.ui.candleChart.addPriceSecondaryY( refPrice, index=tickerIndex, set_label=False )

        timeData = list(timeColumn)
        self.ui.candleChart.addPriceLine( timeData, priceColumn, color='#FF000055', index=tickerIndex )

        self.ui.candleChart.addPriceHLine( refPrice, color='r', index=tickerIndex )

        ## add wallet points
        self._addWalletData( intraSource, self.ui.candleChart, tickerIndex )

        closeColumn  = candleFrame["Close"]
        recentPrice = closeColumn.iloc[-1]
        self.ui.candleChart.addVolumeSecondaryY( recentPrice, index=tickerIndex, set_label=False )

        returnParamsDict = {}
        paramsDict = { "ylabel": "",
                       "ylabel_lower": "",
                       "axtitle": title,
                       "xlim": (minTransTime, maxTransTime),
                       "return_calculated_values": returnParamsDict,
                       "returnfig": True
                       }
        self.ui.candleChart.addPriceCandles( candleFrame, index=tickerIndex, paramsDict=paramsDict )

        clear_labels( pricePlot )
        clear_labels( volumePlot )

        candlestickchart.set_ref_format_coord( pricePlot, refPrice )
        candlestickchart.set_int_format_coord( volumePlot )

    def _addWalletData(self, intraSource, chart, tickerIndex):
        ticker_pair = self.tickerList[ tickerIndex ]
        ticker       = ticker_pair[0]

        dataFrame = intraSource.getWorksheetData()
        timeColumn = dataFrame["t"]
        timeData = list(timeColumn)
#         refX = [ timeData[0], timeData[-1] ]

        transMode = self.dataObject.transactionsMatchMode()
        walletStock: TransHistory = self.dataObject.wallet[ ticker ]
        if walletStock is not None:
            if self.ui.showWalletCB.isChecked():
                amount, buy_unit_price = walletStock.currentTransactionsAvg( transMode )
                if amount > 0:
#                     refY = [ buy_unit_price, buy_unit_price ]
#                     chart.addPriceLine( refX, refY, color='black', style="--" )
                    chart.addPriceHLine( buy_unit_price, color='black', index=tickerIndex )

            if self.ui.showTransactionsLevelsCB.isChecked():
                currTransactions = walletStock.currentTransactions( transMode )
                for item in currTransactions:
                    buy_unit_price = item.unitPrice
#                     refY = [ buy_unit_price, buy_unit_price ]
#                     chart.addPriceLine( refX, refY, color='blue', style="--" )
                    chart.addPriceHLine( buy_unit_price, color='blue', index=tickerIndex )

            if self.ui.showTransactionsPointsCB.isChecked():
                allTransactions = walletStock.allTransactions()
                for item in allTransactions:
                    trans_time     = item.transTime
                    if trans_time < timeData[0]:
                        continue
                    amount         = item.amount
                    buy_unit_price = item.unitPrice
                    if amount > 0:
                        chart.addPricePoint( trans_time, buy_unit_price, color='blue', annotation="+", index=tickerIndex )
                    else:
                        chart.addPricePoint( trans_time, buy_unit_price, color='blue', annotation="-", index=tickerIndex )

    def _dataSourceObjectsList(self):
        retList = []

        for ticker_pair in self.tickerList:
            ticker = ticker_pair[0]
            isin = self.dataObject.getStockIsinFromTicker( ticker )

            ## current range item
            rangeText = self.ui.rangeCB.currentText()
            intraSource = self.dataObject.gpwStockIntradayData.getSource( isin, rangeText )
            retList.append( intraSource )

            ## all range items
#             for i in range(0, self.ui.rangeCB.count()):
#                 rangeText = self.ui.rangeCB.itemText( i )
#                 intraSource = self.dataObject.gpwStockIntradayData.getSource( isin, rangeText )
#                 retList.append( intraSource )

        currentData = self.getCurrentDataSource()
        retList.append( currentData )

        return retList

    def _refreshTickersList(self):
        namesList = list()
        currentSource: GpwCurrentStockData = self.getCurrentDataSource()
        for ticker_pair in self.tickerList:
            ticker = ticker_pair[0]
            name   = currentSource.getNameFromTicker( ticker )
            change = currentSource.getRecentChangeByTicker( ticker )
            namesList.append( (ticker, name, change) )
        self.tickerList = namesList

    def getIntradayDataSource(self, ticker) -> GpwCurrentStockIntradayData:
        rangeText = self.ui.rangeCB.currentText()
        isin = self.dataObject.getStockIsinFromTicker( ticker )
        intraSource = self.dataObject.gpwStockIntradayData.getSource( isin, rangeText )
        return intraSource

    def getCurrentDataSource(self) -> GpwCurrentStockData:
        return self.dataObject.gpwCurrentData

    def closeChart(self):
        if not self.dataObject:
            return
        for ticker_pair in self.tickerList:
            ticker = ticker_pair[0]
            isin = self.dataObject.getStockIsinFromTicker( ticker )
            dataMap: GpwStockIntradayMap = self.dataObject.gpwStockIntradayData
            dataMap.deleteData( isin )

#     def resizeEvent(self, event ):
#         newWidth = self.ui.candleChart.width()
#         subplotWidth = newWidth / self.ui.candleChart.colsNum
#         newBins = int( subplotWidth / 14 )
#         if self._currBinsNum != newBins:
#             self._currBinsNum = newBins
#             self._updateView()

    def resizeEvent( self, event ):
        newWidth = self.width()
        subplotWidth = newWidth / self.ui.candleChart.colsNum
        newBins = int( subplotWidth / 14 )
        if self._currBinsNum != newBins:
            self._currBinsNum = newBins
            if self._updateTimerId > 0:
                self.killTimer( self._updateTimerId )
            self._updateTimerId = self.startTimer( 500 )
        super().resizeEvent( event )

    def timerEvent( self, event ):
        self.killTimer( event.timerId() )
        self._updateTimerId = 0
        self._updateView()


def create_window( dataObject, tickerList, parent=None ):
    chartWindow = ChartAppWindow( parent )
    chart = StockMosaicWidget( chartWindow )
    chartWindow.addWidget( chart )
    chartWindow.refreshAction.triggered.connect( chart.refreshData )
    chartWindow.windowClosed.connect( chart.closeChart )

    chart.connectData( dataObject, tickerList )

    title = ""
    for ticker in tickerList:
        title += ticker + " "
    chartWindow.setWindowTitleSuffix( "- " + title )
    chart.ui.stockLabel.setText( title )

    chartWindow.resize( 1200, 800 )
    chartWindow.show()

#     chart.updateData( access=True )
    return chartWindow


def clear_labels( plot ):
#     plot.set_axis_off()
    plot.set_xticks( [] )
    plot.set_yticks( [] )
    plot.set_ylabel( "" )
