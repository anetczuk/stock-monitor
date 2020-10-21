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

from stockmonitor.gui.appwindow import AppWindow
from stockmonitor.gui.utils import set_label_url
from stockmonitor.gui import threadlist
from stockmonitor.gui.widget.mpl.baseintradaychart import set_ref_format_coord

from .. import uiloader

from .mpl.mpltoolbar import NavigationToolbar


_LOGGER = logging.getLogger(__name__)


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class IndexChartWidget(QtBaseClass):                    # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.dataObject = None
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

    def connectData(self, dataObject, isin):
        self.dataObject = dataObject
        self.isin       = isin
        self.dataObject.stockDataChanged.connect( self.updateData )
        self.updateData( True )

    def clearData(self):
        self.ui.dataChart.clearPlot()

    def refreshData(self):
        self.updateData( True )

    def repaintData(self):
        self.updateData( False )

    def updateData(self, forceRefresh=False):
        self.ui.refreshPB.setEnabled( False )

        threads = threadlist.QThreadMeasuredList( self )
        threads.finished.connect( threads.deleteLater )
        threads.finished.connect( self._updateView, Qt.QueuedConnection )

        intraSource = self.getIntradayDataSource()
        threads.appendFunction( intraSource.getWorksheet, [forceRefresh] )

        currentData = self.getCurrentDataSource()
        threads.appendFunction( currentData.loadWorksheet, [forceRefresh] )

        threads.start()

    def _updateView(self):
        self.ui.refreshPB.setEnabled( True )

        rangeText = self.ui.rangeCB.currentText()
        _LOGGER.debug( "updating chart data, range[%s]", rangeText )

        intraSource = self.getIntradayDataSource()
        dataFrame = intraSource.getWorksheet()

        self.clearData()
        if dataFrame is None:
            return

        currentSource = self.getCurrentDataSource()
        currentSource.loadWorksheet()

#         print( "got intraday data:", dataFrame )
        timeColumn   = dataFrame["t"]
        priceColumn  = dataFrame["c"]

        value     = currentSource.getRecentValue( self.isin )
        change    = currentSource.getRecentChange( self.isin )
        refPrice  = priceColumn[ 0 ]
        timestamp = timeColumn.iloc[-1]

        timeData = list(timeColumn)
        self.ui.dataChart.addPriceLine( timeData, priceColumn )

        self.ui.dataChart.addPriceSecondaryY( refPrice )

        refX = [ timeData[0], timeData[-1] ]
        refY = [ refPrice, refPrice ]
        self.ui.dataChart.addPriceLine( refX, refY, style="--" )

        set_ref_format_coord( self.ui.dataChart.pricePlot, refPrice )

        self.ui.valueLabel.setText( str(value) )
        self.ui.changeLabel.setText( str(change) + "%" )
        self.ui.timeLabel.setText( str(timestamp) )

        set_label_url( self.ui.sourceLabel, intraSource.sourceLink() )

    def getIntradayDataSource(self):
        rangeText = self.ui.rangeCB.currentText()
        intraSource = self.dataObject.gpwIndexIntradayData.getSource( self.isin, rangeText )
        return intraSource

    def getCurrentDataSource(self):
        return self.dataObject.gpwIndexesData


def create_window( dataObject, isin, parent=None ):
    chartWindow = AppWindow( parent )
    chart = IndexChartWidget( chartWindow )
    chartWindow.addWidget( chart )
    chartWindow.refreshAction.triggered.connect( chart.refreshData )

    chart.connectData(dataObject, isin)

    currentSource = chart.getCurrentDataSource()
    name = currentSource.getNameFromIsin( isin )
    title = name + " [" + isin + "]"
    chartWindow.setWindowTitleSuffix( "- " + title )
    chart.ui.nameLabel.setText( name )

    chartWindow.show()

    return chartWindow
