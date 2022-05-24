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

from stockmonitor.datatypes.stocktypes import GpwStockIntradayMap
from stockmonitor.datatypes.wallettypes import TransHistory
from stockmonitor.dataaccess.gpw.gpwcurrentdata import GpwCurrentStockData
from stockmonitor.gui import threadlist
from stockmonitor.gui.dataobject import DataObject
from stockmonitor.gui.appwindow import ChartAppWindow
from stockmonitor.gui.utils import set_label_url
from stockmonitor.gui.widget.mpl import mplbasechart
from stockmonitor.dataaccess.gpw.gpwintradaydata import GpwCurrentStockIntradayData
from stockmonitor.gui.widget.mpl import candlestickchart

from .. import uiloader

from .mpl.mpltoolbar import NavigationToolbar
import datetime


_LOGGER = logging.getLogger(__name__)


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class StockChartWidget(QtBaseClass):                    # type: ignore
    ## double, price and volumen chart

#     updateFinished = QtCore.pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.dataObject: DataObject = None
        self.ticker = None
        self._currBinsNum = 100
        self._updateTimerId = 0

        if parentWidget is not None:
            bgcolor = parentWidget.palette().color(parentWidget.backgroundRole())
            self.ui.dataChart.setBackgroundByQColor( bgcolor )
            self.ui.candleChart.setBackgroundByQColor( bgcolor )

        self.ui.candleChart.generateMosaic( 1, 1 )

        self.toolbar = None
        self._changeChartType()

        self.ui.sourceLabel.setOpenExternalLinks(True)

        self.ui.stockLabel.setStyleSheet("font-weight: bold")

        self.ui.showWalletCB.setChecked( False )
        self.ui.showWalletCB.stateChanged.connect( self.repaintData )
        self.ui.showTransactionsLevelsCB.setChecked( False )
        self.ui.showTransactionsLevelsCB.stateChanged.connect( self.repaintData )
        self.ui.showTransactionsPointsCB.setChecked( True )
        self.ui.showTransactionsPointsCB.stateChanged.connect( self.repaintData )

        self.ui.refreshPB.clicked.connect( self.refreshData )
        self.ui.rangeCB.currentIndexChanged.connect( self.repaintData )
        self.ui.chartTypeCB.currentIndexChanged.connect( self._changeChartType )

    def connectData(self, dataObject: DataObject, ticker):
        self.dataObject = dataObject
        self.ticker     = ticker
        self.dataObject.stockDataChanged.connect( self.updateData )
#         self.updateData( False )

    def clearData(self):
        self.ui.dataChart.clearPlot()
        self.ui.candleChart.clearPlot()

    def refreshData(self):
        self.updateData( True )

    def repaintData(self):
        self.updateData( False )

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

        ThreadingListType = threadlist.get_threading_list()
        threads = ThreadingListType( self )
        threads.finished.connect( self._updateView )
        threads.deleteOnFinish()

        for source in dataSources:
            if access is False:
                threads.appendFunction( source.getWorksheetData, [forceRefresh] )
            else:
                threads.appendFunction( source.accessWorksheetData, [forceRefresh] )

        threads.start()

    # pylint: disable=R0914
    def _updateView(self):
        self.ui.refreshPB.setEnabled( True )

        rangeText = self.ui.rangeCB.currentText()
        isin = self.dataObject.getStockIsinFromTicker( self.ticker )
        _LOGGER.debug( "updating chart data, range[%s] isin[%s]", rangeText, isin )

        self.clearData()

        intraSource: GpwCurrentStockIntradayData = self.getIntradayDataSource()
        dataFrame = intraSource.getWorksheetData()

        if dataFrame is None:
            return

        currentSource: GpwCurrentStockData = self.getCurrentDataSource()
        currentSource.getWorksheetData()

        timeColumn   = dataFrame["t"]
        volumeColumn = dataFrame["v"]

        price     = currentSource.getRecentValueByTicker( self.ticker )
        change    = currentSource.getRecentChangeByTicker( self.ticker )
        volumen   = volumeColumn.iloc[-1]
        timestamp = timeColumn.iloc[-1]

        self.ui.valueLabel.setText( str(price) )
        self.ui.changeLabel.setText( str(change) + "%" )
        self.ui.volumeLabel.setText( str(volumen) )
        self.ui.timeLabel.setText( str(timestamp) )

        if self.ui.dataChart.isVisible():
            self._updateLineChart( intraSource )

        if self.ui.candleChart.isVisible():
            self._updateCandleChart( intraSource )

        set_label_url( self.ui.sourceLabel, intraSource.sourceLink() )

    def _updateLineChart(self, intraSource):
        dataFrame = intraSource.getWorksheetData()

        timeColumn   = dataFrame["t"]
        priceColumn  = dataFrame["c"]
        volumeColumn = dataFrame["v"]
#         print( "got intraday data:", priceColumn )

        currentSource: GpwCurrentStockData = self.getCurrentDataSource()
        currentSource.getWorksheetData()

        refPrice = currentSource.getReferenceValueByTicker( self.ticker )

        self.ui.dataChart.addPriceSecondaryY( refPrice )

        timeData = list(timeColumn)
        self.ui.dataChart.addPriceLine( timeData, priceColumn )

        self.ui.dataChart.addPriceHLine( refPrice, style="--" )

        ## add wallet points
        self._addWalletData( intraSource, self.ui.dataChart )

        self.ui.dataChart.addVolumeLine( timeData, volumeColumn )

        recentPrice = priceColumn.iloc[-1]
        self.ui.dataChart.addVolumeSecondaryY( recentPrice )

        mplbasechart.set_ref_format_coord( self.ui.dataChart.pricePlot, refPrice )
        mplbasechart.set_int_format_coord( self.ui.dataChart.volumePlot )

    def _updateCandleChart( self, intraSource: GpwCurrentStockIntradayData ):
        ## get data
        ##intraSource = self.dataObject.gpwStockIntradayData.getSource( isin, rangeText )
        ##return intraSource

        candleFrame = prepare_candle_data( intraSource, self._currBinsNum )
        if candleFrame is None or len( candleFrame ) < 2:
            ## no data to show
            return

        dataFrame = intraSource.getWorksheetData()

        timeColumn   = candleFrame.index
        priceColumn  = candleFrame["Close"]

        currentSource: GpwCurrentStockData = self.getCurrentDataSource()
        refPrice = currentSource.getReferenceValueByTicker( self.ticker )

        self.ui.candleChart.addPriceSecondaryY( refPrice )

        timeData = list(timeColumn)
        self.ui.candleChart.addPriceLine( timeData, priceColumn, color='#FF000088' )

        self.ui.candleChart.addPriceHLine( refPrice, color='r' )

        ## add wallet points
        self._addWalletData( intraSource, self.ui.candleChart )

        closeColumn  = dataFrame["c"]
        recentPrice = closeColumn.iloc[-1]
        self.ui.candleChart.addVolumeSecondaryY( recentPrice )

#         paramsDict = {}
#         timeSpan = timeData[-1] - timeData[0]
#         if timeSpan > datetime.timedelta( days=66 ):
#             paramsDict[ "show_nontrading" ] = False
#         paramsDict[ "show_nontrading" ] = False
#         self.ui.candleChart.addPriceCandles( candleFrame, paramsDict=paramsDict )
        self.ui.candleChart.addPriceCandles( candleFrame )

        self.ui.candleChart.refreshCanvas()

        pricePlot  = self.ui.candleChart.getPricePlot()
        volumePlot = self.ui.candleChart.getVolumePlot()
        candlestickchart.set_ref_format_coord( pricePlot, refPrice )
        candlestickchart.set_int_format_coord( volumePlot )

    def _addWalletData(self, intraSource, chart):
        dataFrame = intraSource.getWorksheetData()
        timeColumn = dataFrame["t"]
        timeData = list(timeColumn)
#         refX = [ timeData[0], timeData[-1] ]

        transMode = self.dataObject.transactionsMatchMode()
        walletStock: TransHistory = self.dataObject.wallet[ self.ticker ]
        if walletStock is not None:
            if self.ui.showWalletCB.isChecked():
                amount, buy_unit_price = walletStock.currentTransactionsAvg( transMode )
                if amount > 0:
#                     refY = [ buy_unit_price, buy_unit_price ]
#                     chart.addPriceLine( refX, refY, color='black', style="--" )
                    chart.addPriceHLine( buy_unit_price, color='black' )

            if self.ui.showTransactionsLevelsCB.isChecked():
                currTransactions = walletStock.currentTransactions( transMode )
                for item in currTransactions:
                    buy_unit_price = item.unitPrice
#                     refY = [ buy_unit_price, buy_unit_price ]
#                     chart.addPriceLine( refX, refY, color='blue', style="--" )
                    chart.addPriceHLine( buy_unit_price, color='blue' )

            if self.ui.showTransactionsPointsCB.isChecked():
                allTransactions = walletStock.allTransactions()
                for item in allTransactions:
                    trans_time     = item.transTime
                    if trans_time < timeData[0]:
                        continue
                    amount         = item.amount
                    buy_unit_price = item.unitPrice
                    if amount > 0:
                        chart.addPricePoint( trans_time, buy_unit_price, color='blue', annotation="+" )
                    else:
                        chart.addPricePoint( trans_time, buy_unit_price, color='blue', annotation="-" )

#     def _getArchiveCandlesData( self ):
#         rangeText     = self.ui.rangeCB.currentText()
#         startDateTime = get_start_date( rangeText )
#         start_date    = startDateTime.date()
#
#         isin = self.dataObject.getStockIsinFromTicker( self.ticker )
#
#         openIndex   = GpwArchiveData.getColumnIndex( StockDataType.OPENING )
#         highIndex   = GpwArchiveData.getColumnIndex( StockDataType.MAX )
#         lowIndex    = GpwArchiveData.getColumnIndex( StockDataType.MIN )
#         closeIndex  = GpwArchiveData.getColumnIndex( StockDataType.CLOSING )
#         volumeIndex = GpwArchiveData.getColumnIndex( StockDataType.VOLUME )
#
#         holidayCalendar = HolidayData()
#
#         timestamps = []
#         frame = { 'Open': [], 'High': [], 'Low': [], 'Close': [], 'Volume': [] }
#         end_date = datetime.datetime.now().date()
#         delta    = datetime.timedelta(days=1)
#         curr_date = start_date
#         while curr_date < end_date:
#             if holidayCalendar.isHoliday( curr_date ):
#                 curr_date += delta
#                 continue
#
#             archiveData = GpwArchiveData( curr_date )
#             dataFrame = archiveData.accessWorksheetData()
#             # dataFrame = archiveData.loadWorksheet( preventDownload=True )
#
#             if dataFrame is None:
#                 #print( "holiday?", dataFrame )
#                 holidayCalendar.markHoliday( curr_date )
#
#             isinRow = archiveData.getRowByIsin(isin)
#             if isinRow is None:
#                 curr_date += delta
#                 continue
#             if isinRow.empty is True:
#                 curr_date += delta
#                 continue
#
#             timestamps.append( curr_date )
#             curr_date += delta
#
#             frame[ 'Open' ].append( isinRow[openIndex] )
#             frame[ 'High' ].append( isinRow[highIndex] )
#             frame[ 'Low' ].append( isinRow[lowIndex] )
#             frame[ 'Close' ].append( isinRow[closeIndex] )
#             frame[ 'Volume' ].append( isinRow[volumeIndex] )
#
# #         ## add current values
# #         timestamps.append( curr_date )
# #         frame[ 'Open' ].append( isinRow[openIndex] )
# #         frame[ 'High' ].append( isinRow[highIndex] )
# #         frame[ 'Low' ].append( isinRow[lowIndex] )
# #         frame[ 'Close' ].append( isinRow[closeIndex] )
# #         frame[ 'Volume' ].append( isinRow[volumeIndex] )
#
#         dataframe = pandas.DataFrame( frame )
#         dataframe.index = pandas.DatetimeIndex( timestamps )
#         return dataframe

    def _dataSourceObjectsList(self):
        retList = []
        isin = self.dataObject.getStockIsinFromTicker( self.ticker )
        for i in range(0, self.ui.rangeCB.count()):
            rangeText = self.ui.rangeCB.itemText( i )
            intraSource = self.dataObject.gpwStockIntradayData.getSource( isin, rangeText )
            retList.append( intraSource )

        currentData = self.getCurrentDataSource()
        retList.append( currentData )
        return retList

    def getIntradayDataSource(self) -> GpwCurrentStockIntradayData:
        rangeText = self.ui.rangeCB.currentText()
        isin = self.dataObject.getStockIsinFromTicker( self.ticker )
        intraSource = self.dataObject.gpwStockIntradayData.getSource( isin, rangeText )
        return intraSource

    def getCurrentDataSource(self) -> GpwCurrentStockData:
        return self.dataObject.gpwCurrentData

    def deleteData(self):
        if self.dataObject:
            isin = self.dataObject.getStockIsinFromTicker( self.ticker )
            dataMap: GpwStockIntradayMap = self.dataObject.gpwStockIntradayData
            dataMap.deleteData( isin )

    def _changeChartType(self):
        typeText = self.ui.chartTypeCB.currentText()
        if typeText == "Line":
            self.ui.dataChart.show()
            self.ui.candleChart.hide()

            layoutItems = self.ui.toolbarLayout.count()
            for i in range(0, layoutItems):
                itemWidget = self.ui.toolbarLayout.itemAt( i ).widget()
                if itemWidget is None:
                    continue
                itemWidget.deleteLater()

            if self.toolbar is not None:
                del self.toolbar
            self.toolbar = NavigationToolbar(self.ui.dataChart, self)
            self.ui.toolbarLayout.addWidget( self.toolbar )

        else:
            self.ui.dataChart.hide()
            self.ui.candleChart.show()

            layoutItems = self.ui.toolbarLayout.count()
            for i in range(0, layoutItems):
                itemWidget = self.ui.toolbarLayout.itemAt( i ).widget()
                if itemWidget is None:
                    continue
                itemWidget.deleteLater()

            if self.toolbar is not None:
                del self.toolbar
            self.toolbar = NavigationToolbar(self.ui.candleChart, self)
            self.ui.toolbarLayout.addWidget( self.toolbar )

        self.repaintData()

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


def prepare_candle_data( intraSource: GpwCurrentStockIntradayData, bins=None ):
    dataFrame = intraSource.getWorksheetData()
    if dataFrame is None:
        return None

    recalculate = True
    if bins is None:
        recalculate = False
    elif len( dataFrame ) <= bins:
        recalculate = False

    if recalculate is False:
        rename_map = { "o": "Open",
                       "c": "Close",
                       "l": "Low",
                       "h": "High",
                       "v": "Volume"
                       }
        renamedData = dataFrame.rename( columns=rename_map )
        renamedData.index = pandas.DatetimeIndex( renamedData["t"] )
        # renamedData.drop( columns="t", inplace=True )
        return renamedData

    ## calculate bins

    dataFrame[ "bin" ] = pandas.cut( dataFrame["t"], bins=bins, labels=False )

    recent_bin = -1
    timestamps = []
    frame: Dict[ str, List ] = { 'Open': [], 'High': [], 'Low': [], 'Close': [], 'Volume': [] }

    for _, row in dataFrame.iterrows():
        curr_bin = row["bin"]
        if curr_bin != recent_bin:
            recent_bin = curr_bin
            timestamps.append( row["t"] )
            frame[ 'Open' ].append( row["o"] )
            frame[ 'High' ].append( row["h"] )
            frame[ 'Low' ].append( row["l"] )
            frame[ 'Close' ].append( row["c"] )
            frame[ 'Volume' ].append( row["v"] )
            continue

        # frame[ 'Open' ].append( row["o"] )
        frame[ 'High' ][-1]    = max( frame[ 'High' ][-1], row["h"] )
        frame[ 'Low' ][-1]     = min( frame[ 'High' ][-1], row["h"] )
        frame[ 'Close' ][-1]   = row["c"]
        frame[ 'Volume' ][-1] += row["v"]

    retFrame = pandas.DataFrame( frame )
    retFrame.index = pandas.DatetimeIndex( timestamps )
    return retFrame


## repeat last row, set to given time and clear open. hi. lo and volume fields (just indicate current price)
def set_end_row( dataFrame, maxTime ):
    if maxTime is None:
        return dataFrame
    if dataFrame.index[-1] == maxTime:
        return dataFrame

    ## repeat last row and change time value

    newDataFrame = dataFrame.append( dataFrame.iloc[-1] )
    
    ind = newDataFrame.index.tolist()
    ind[ -1 ] = maxTime
    newDataFrame.index = ind
    if 't' in newDataFrame.columns:
        newDataFrame.loc[maxTime, 't'] = maxTime

    closeValue = newDataFrame.loc[maxTime, 'Close']
    newDataFrame.loc[maxTime, 'Open']   = closeValue
    newDataFrame.loc[maxTime, 'High']   = closeValue
    newDataFrame.loc[maxTime, 'Low']    = closeValue
    newDataFrame.loc[maxTime, 'Volume'] = 0

#     print("ggggggg:", newDataFrame)
    return newDataFrame


## ==================================================================


def create_window( dataObject, ticker, parent=None ):
    chartWindow = ChartAppWindow( parent )
    chart = StockChartWidget( chartWindow )
    chartWindow.addWidget( chart )
    chartWindow.refreshAction.triggered.connect( chart.refreshData )
    chartWindow.windowClosed.connect( chart.deleteData )

    chart.connectData(dataObject, ticker)

    name = dataObject.getNameFromTicker( ticker )
    if name is not None:
        title = name + " [" + ticker + "]"
        chartWindow.setWindowTitleSuffix( "- " + title )
        chart.ui.stockLabel.setText( name )

    chartWindow.show()

    chart.updateData( access=True )
    return chartWindow
