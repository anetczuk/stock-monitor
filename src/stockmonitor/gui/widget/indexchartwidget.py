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


class IndexChartWidget(QtBaseClass):                    # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.ui = UiTargetClass()
        self.ui.setupUi(self)

#         self.device = None

        if parentWidget is not None:
            bgcolor = parentWidget.palette().color(parentWidget.backgroundRole())
            self.ui.dataChart.setBackgroundByQColor( bgcolor )

        self.toolbar = DynamicToolbar(self.ui.dataChart, self)
        self.ui.toolbarLayout.addWidget( self.toolbar )

    def clearData(self):
        self.ui.dataChart.clearData()

#     def attachConnector(self, connector):
#         if self.device is not None:
#             ## disconnect old object
#             self.device.connectionStateChanged.disconnect( self._refreshWidget )
#             self.device.positionChanged.disconnect( self._updatePositionState )
#
#         self.device = connector
#
#         self._refreshWidget()
#
#         if self.device is not None:
#             ## connect new object
#             self.device.connectionStateChanged.connect( self._refreshWidget )
#             self.device.positionChanged.connect( self._updatePositionState )

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

    def setData(self, xdata, ydata ):
        self.ui.dataChart.setData( list(xdata), ydata )


class IndexChartWindow( AppWindow ):

    def __init__(self, parentWidget=None):
        super().__init__( parentWidget )

        self.dataObject = None
        self.isin = None

        self.chart = IndexChartWidget( self )
        self.addWidget( self.chart )
        
        self.chart.ui.nameLabel.setStyleSheet("font-weight: bold")

    def connectData(self, dataObject, isin):
        self.dataObject = dataObject
        self.isin       = isin
        self.dataObject.stockDataChanged.connect( self.updateData )
        self._setStockName()
        self.updateData()

    def updateData(self):
        dataFrame = self.dataObject.getIndexIntradayDataByIsin( self.isin )
        if dataFrame is None:
            self.chart.clearData()
            return

#         print( "got intraday data:", dataFrame )
        timeColumn   = dataFrame["t"]
        priceColumn  = dataFrame["c"]
        self.chart.setData( timeColumn, priceColumn )
        
        currentSource = self.dataObject.gpwIndexesData
        value     = currentSource.getRecentValue( self.isin )
        change    = currentSource.getRecentChange( self.isin )
        timestamp = timeColumn.iloc[-1]
 
        self.chart.ui.valueLabel.setText( str(value) )
        self.chart.ui.changeLabel.setText( str(change)+"%" )
        self.chart.ui.timeLabel.setText( str(timestamp) )

    def _setStockName(self):
        currentSource = self.dataObject.gpwIndexesData
        name = currentSource.getNameFromIsin( self.isin )
        title = name + " [" + self.isin + "]"
        self.setWindowTitleSuffix( "- " + title )
        self.chart.ui.nameLabel.setText( name )
