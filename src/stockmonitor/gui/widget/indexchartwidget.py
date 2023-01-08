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
import datetime
from typing import Dict, List

import pandas

from PyQt5.QtCore import Qt

from stockdataaccess.dataaccess.gpw.gpwcurrentdata import GpwCurrentIndexesData
from stockdataaccess.dataaccess.gpw.gpwintradaydata import GpwCurrentIndexIntradayData
from stockmonitor.datatypes.stocktypes import GpwIndexIntradayMap
from stockmonitor.gui.appwindow import ChartAppWindow
from stockmonitor.gui.utils import set_label_url
from stockmonitor.gui import threadlist
from stockmonitor.gui.widget.mpl.mplbasechart import set_ref_format_coord
from stockmonitor.gui.widget.mpl import candlestickchart
from stockmonitor.gui.dataobject import DataObject

from .. import uiloader

from .mpl.mpltoolbar import NavigationToolbar


_LOGGER = logging.getLogger(__name__)


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class IndexChartWidget(QtBaseClass):                    # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.dataObject: DataObject = None
        self.isin = None

        if parentWidget is not None:
            bgcolor = parentWidget.palette().color(parentWidget.backgroundRole())
            self.ui.dataChart.setBackgroundByQColor( bgcolor )
            self.ui.candleChart.setBackgroundByQColor( bgcolor )

        self.toolbar = None
        self._changeChartType()

        self.ui.sourceLabel.setOpenExternalLinks(True)

        self.ui.nameLabel.setStyleSheet("font-weight: bold")

        self.ui.refreshPB.clicked.connect( self.refreshData )
        self.ui.rangeCB.currentIndexChanged.connect( self.repaintData )
        self.ui.chartTypeCB.currentIndexChanged.connect( self._changeChartType )

        ThreadingListType = threadlist.get_threading_list_class()
        self.threads = ThreadingListType( self )
        self.threads.finished.connect( self._updateView )
        # self.threads.deleteOnFinish()

    def connectData(self, dataObject: DataObject, isin):
        self.dataObject = dataObject
        self.isin       = isin
        self.dataObject.stockDataChanged.connect( self.updateData )
        self.updateData( False )

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

        call_list = []
        for source in dataSources:
            if access is False:
                call_list.append( [ source.getWorksheetData, [forceRefresh] ] )
                # self.threads.appendFunction( source.getWorksheetData, [forceRefresh] )
            else:
                call_list.append( [ source.accessWorksheetData, [forceRefresh] ] )
                # self.threads.appendFunction( source.accessWorksheetData, [forceRefresh] )

        self.threads.start( call_list )

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

    def _dataSourceObjectsList(self):
        ## iterate through ranges values and collect data sources
        retList = []
        indexData: GpwIndexIntradayMap = self.dataObject.gpwIndexIntradayData
        for i in range(0, self.ui.rangeCB.count()):
            rangeText = self.ui.rangeCB.itemText( i )
            intraSource: GpwCurrentIndexIntradayData = indexData.getSource( self.isin, rangeText )
            retList.append( intraSource )

        currentData = self.getCurrentDataSource()
        retList.append( currentData )
        return retList

    def _updateView(self):
        self.ui.refreshPB.setEnabled( True )

        rangeText = self.ui.rangeCB.currentText()
        _LOGGER.debug( "updating chart data, range[%s]", rangeText )

        self.clearData()

        intraSource = self.getIntradayDataSource()
        dataFrame = intraSource.getWorksheetData()

        if dataFrame is None:
            return

        currentSource: GpwCurrentIndexesData = self.getCurrentDataSource()
        currentSource.getWorksheetData()

        timeColumn   = dataFrame["t"]

        value     = currentSource.getRecentValueByIsin( self.isin )
        change    = currentSource.getRecentChangeByIsin( self.isin )
        timestamp = timeColumn.iloc[-1]

        self.ui.valueLabel.setText( str(value) )
        self.ui.changeLabel.setText( str(change) + "%" )
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

        currentSource: GpwCurrentIndexesData = self.getCurrentDataSource()
        currentSource.getWorksheetData()

#         refPrice = priceColumn[ 0 ]
        refPrice = self.getReferenceValue()
        self.ui.dataChart.addPriceSecondaryY( refPrice )

        timeData = list(timeColumn)
        self.ui.dataChart.addPriceLine( timeData, priceColumn )

        self.ui.dataChart.addPriceHLine( refPrice, style="--" )

        currTime = datetime.datetime.now() - datetime.timedelta(minutes=15)
        if timeData[0] < currTime < timeData[-1]:
            self.ui.dataChart.pricePlot.axvline( x=currTime, color="black", linestyle="--" )

        set_ref_format_coord( self.ui.dataChart.pricePlot, refPrice )

    def _updateCandleChart( self, intraSource ):
        ## get data
        ##intraSource = self.dataObject.gpwStockIntradayData.getSource( isin, rangeText )
        ##return intraSource

        candleFrame = self._getCurrentCandlesData( intraSource, 100 )
        if candleFrame is None or len( candleFrame ) < 2:
            ## no data to show
            return

        timeColumn   = candleFrame.index
        priceColumn  = candleFrame["Close"]

#         refPrice = priceColumn[ 0 ]
        refPrice = self.getReferenceValue()

        self.ui.candleChart.addPriceSecondaryY( refPrice )

        timeData = list(timeColumn)
        self.ui.candleChart.addPriceLine( timeData, priceColumn, color='#FF000088' )

        self.ui.candleChart.addPriceHLine( refPrice, color='y' )

        self.ui.candleChart.addPriceCandles( candleFrame )

        self.ui.candleChart.refreshCanvas()

        candlestickchart.set_ref_format_coord( self.ui.candleChart.pricePlot, refPrice )

    def _getCurrentCandlesData( self, intraSource, bins=None ):
        dataFrame = intraSource.getWorksheetData()

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
        frame: Dict[ str, List ] = { 'Open': [], 'High': [], 'Low': [], 'Close': [] }

        for _, row in dataFrame.iterrows():
            curr_bin = row["bin"]
            if curr_bin != recent_bin:
                recent_bin = curr_bin
                timestamps.append( row["t"] )
                frame[ 'Open' ].append( row["o"] )
                frame[ 'High' ].append( row["h"] )
                frame[ 'Low' ].append( row["l"] )
                frame[ 'Close' ].append( row["c"] )
                continue

            # frame[ 'Open' ].append( row["o"] )
            frame[ 'High' ][-1]    = max( frame[ 'High' ][-1], row["h"] )
            frame[ 'Low' ][-1]     = min( frame[ 'High' ][-1], row["h"] )
            frame[ 'Close' ][-1]   = row["c"]

        dataframe = pandas.DataFrame( frame )
        dataframe.index = pandas.DatetimeIndex( timestamps )
        return dataframe

    def getReferenceValue(self):
        indexData: GpwIndexIntradayMap = self.dataObject.gpwIndexIntradayData
        intraSource = indexData.getSource( self.isin, "14D" )
        dataFrame = intraSource.getWorksheetData()
        if dataFrame is None:
            return None
        priceColumn = dataFrame["c"]

        timeColumn  = dataFrame["t"]
        recentTime  = timeColumn.iloc[-1]
        recentDate = recentTime.date()
        currDate = datetime.datetime.now().date()
        if recentDate == currDate:
            ## after end of session, but the same day
            return priceColumn.iloc[-2]
        ## during the session or before the session
        return priceColumn.iloc[-1]

    def getIntradayDataSource(self):
        rangeText = self.ui.rangeCB.currentText()
        indexData = self.dataObject.gpwIndexIntradayData
        intraSource = indexData.getSource( self.isin, rangeText )
        return intraSource

    def getCurrentDataSource(self) -> GpwCurrentIndexesData:
        return self.dataObject.gpwIndexesData

    def closeChart(self):
        ## prevent segfault (calling C++ released object)
        self.threads.stopExecution()

        if self.dataObject:
            dataMap: GpwIndexIntradayMap = self.dataObject.gpwIndexIntradayData
            dataMap.deleteData( self.isin )


def create_window( dataObject, isin, parent=None ):
    chartWindow = ChartAppWindow( parent )
    chart = IndexChartWidget( chartWindow )
    chartWindow.addWidget( chart )
    chartWindow.refreshAction.triggered.connect( chart.refreshData )
    chartWindow.windowClosed.connect( chart.closeChart )

    chart.connectData(dataObject, isin)

    currentSource = chart.getCurrentDataSource()
    name = currentSource.getNameFromIsin( isin )
    title = name + " [" + isin + "]"
    chartWindow.setWindowTitleSuffix( "- " + title )
    chart.ui.nameLabel.setText( name )

    chartWindow.show()

    chart.updateData( access=True )

    return chartWindow
