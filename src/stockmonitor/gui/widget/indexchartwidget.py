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

from PyQt5 import QtWidgets, QtGui

from stockmonitor.gui.appwindow import AppWindow

from .. import uiloader

from .mpl.mpltoolbar import DynamicToolbar


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

        self.toolbar = DynamicToolbar(self.ui.dataChart, self)
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
        self.ui.dataChart.clearLines()

    def refreshData(self):
        self.updateData( True )

    def repaintData(self):
        self.updateData( False )

    def updateData(self, forceRefresh=False):
        rangeText = self.ui.rangeCB.currentText()
        _LOGGER.debug( "updating chart data, force[%s] range[%s]", forceRefresh, rangeText )
        intraSource = self.dataObject.gpwIndexIntradayData.getSource( self.isin, rangeText )
        dataFrame = intraSource.getWorksheet( forceRefresh )

        self.clearData()
        if dataFrame is None:
            return

#         print( "got intraday data:", dataFrame )
        timeColumn   = dataFrame["t"]
        priceColumn  = dataFrame["c"]

        timeData = list(timeColumn)
        self.addPriceLine( timeData, priceColumn )

        currentSource = self.dataObject.gpwIndexesData
        currentSource.loadWorksheet( forceRefresh )

        value     = currentSource.getRecentValue( self.isin )
        change    = currentSource.getRecentChange( self.isin )
        timestamp = timeColumn.iloc[-1]

        self.ui.valueLabel.setText( str(value) )
        self.ui.changeLabel.setText( str(change) + "%" )
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


class IndexChartWindow( AppWindow ):

    def __init__(self, parentWidget=None):
        super().__init__( parentWidget )

        self.chart = IndexChartWidget( self )
        self.addWidget( self.chart )
        
        self.refreshAction = QtWidgets.QAction(self)
        self.refreshAction.setShortcuts( QtGui.QKeySequence.Refresh )
        self.refreshAction.triggered.connect( self.chart.refreshData )
        self.addAction( self.refreshAction )

    def connectData(self, dataObject, isin):
        self.chart.connectData( dataObject, isin )
        self._setStockName()

    def _setStockName(self):
        currentSource = self.chart.dataObject.gpwIndexesData
        name = currentSource.getNameFromIsin( self.chart.isin )
        title = name + " [" + self.chart.isin + "]"
        self.setWindowTitleSuffix( "- " + title )
        self.chart.ui.nameLabel.setText( name )
