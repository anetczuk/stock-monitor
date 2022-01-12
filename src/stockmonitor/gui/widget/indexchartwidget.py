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

from PyQt5.QtCore import Qt

from stockmonitor.dataaccess.gpw.gpwcurrentdata import GpwCurrentIndexesData
from stockmonitor.gui.appwindow import ChartAppWindow
from stockmonitor.gui.utils import set_label_url
from stockmonitor.gui import threadlist
from stockmonitor.gui.widget.mpl.baseintradaychart import set_ref_format_coord

from .. import uiloader

from .mpl.mpltoolbar import NavigationToolbar
from stockmonitor.gui.dataobject import DataObject


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

        self.toolbar = NavigationToolbar(self.ui.dataChart, self)
        self.ui.toolbarLayout.addWidget( self.toolbar )

        self.ui.sourceLabel.setOpenExternalLinks(True)

        self.ui.nameLabel.setStyleSheet("font-weight: bold")

        self.ui.refreshPB.clicked.connect( self.refreshData )
        self.ui.rangeCB.currentIndexChanged.connect( self.repaintData )

    def connectData(self, dataObject: DataObject, isin):
        self.dataObject: DataObject = dataObject
        self.isin       = isin
        self.dataObject.stockDataChanged.connect( self.updateData )
        self.updateData( False )

    def clearData(self):
        self.ui.dataChart.clearPlot()

    def refreshData(self):
        self.updateData( True )

    def repaintData(self):
        self.updateData( False )

    def updateData(self, forceRefresh=False, access=False):
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

        threads = threadlist.QThreadMeasuredList( self )
        threads.finished.connect( threads.deleteLater )
        threads.finished.connect( self._updateView, Qt.QueuedConnection )

        for source in dataSources:
            if access is False:
                threads.appendFunction( source.getWorksheetData, [forceRefresh] )
            else:
                threads.appendFunction( source.accessWorksheetData, [forceRefresh] )

        threads.start()
        
    def _dataSourceObjectsList(self):
        retList = []
        for i in range(0, self.ui.rangeCB.count()):
            rangeText = self.ui.rangeCB.itemText( i )
            indexData: GpwIndexIntradayMap = self.dataObject.gpwIndexIntradayData
            intraSource: GpwCurrentIndexIntradayData = indexData.getSource( self.isin, rangeText )
            retList.append( intraSource )
            
        currentData = self.getCurrentDataSource()
        retList.append( currentData )
        return retList

    def _updateView(self):
        self.ui.refreshPB.setEnabled( True )

        rangeText = self.ui.rangeCB.currentText()
        _LOGGER.debug( "updating chart data, range[%s]", rangeText )

        intraSource = self.getIntradayDataSource()
        dataFrame = intraSource.getWorksheetData()

        self.clearData()
        if dataFrame is None:
            return

        currentSource: GpwCurrentIndexesData = self.getCurrentDataSource()
        currentSource.getWorksheetData()

#         print( "got intraday data:", dataFrame )
        timeColumn   = dataFrame["t"]
        priceColumn  = dataFrame["c"]

        value     = currentSource.getRecentValueByIsin( self.isin )
        change    = currentSource.getRecentChangeByIsin( self.isin )
        timestamp = timeColumn.iloc[-1]

        timeData = list(timeColumn)
        self.ui.dataChart.addPriceLine( timeData, priceColumn )

#         refPrice = priceColumn[ 0 ]
        refPrice = self.getReferenceValue()
        self.ui.dataChart.addPriceSecondaryY( refPrice )

        refX = [ timeData[0], timeData[-1] ]
        refY = [ refPrice, refPrice ]
        self.ui.dataChart.addPriceLine( refX, refY, style="--" )

        currTime = datetime.datetime.now() - datetime.timedelta(minutes=15)
        if currTime < timeData[-1] and currTime > timeData[0]:
            self.ui.dataChart.pricePlot.axvline( x=currTime, color="black", linestyle="--" )

        set_ref_format_coord( self.ui.dataChart.pricePlot, refPrice )

        self.ui.valueLabel.setText( str(value) )
        self.ui.changeLabel.setText( str(change) + "%" )
        self.ui.timeLabel.setText( str(timestamp) )

        set_label_url( self.ui.sourceLabel, intraSource.sourceLink() )

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
    
    def deleteData(self):
        if self.dataObject:
            dataMap: GpwIndexIntradayMap = self.dataObject.gpwIndexIntradayData
            dataMap.deleteData( self.isin )


def create_window( dataObject, isin, parent=None ):
    chartWindow = ChartAppWindow( parent )
    chart = IndexChartWidget( chartWindow )
    chartWindow.addWidget( chart )
    chartWindow.refreshAction.triggered.connect( chart.refreshData )
    chartWindow.windowClosed.connect( chart.deleteData )

    chart.connectData(dataObject, isin)

    currentSource = chart.getCurrentDataSource()
    name = currentSource.getNameFromIsin( isin )
    title = name + " [" + isin + "]"
    chartWindow.setWindowTitleSuffix( "- " + title )
    chart.ui.nameLabel.setText( name )

    chartWindow.show()

    chart.updateData( access=True )

    return chartWindow
