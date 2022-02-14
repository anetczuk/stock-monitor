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
# from PyQt5.QtGui import QCloseEvent

from stockmonitor.datatypes.stocktypes import GpwStockIntradayMap
from stockmonitor.datatypes.wallettypes import TransHistory
from stockmonitor.dataaccess.gpw.gpwcurrentdata import GpwCurrentStockData
from stockmonitor.gui import threadlist
from stockmonitor.gui.dataobject import DataObject
from stockmonitor.gui.appwindow import ChartAppWindow
from stockmonitor.gui.utils import set_label_url
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

        self.dataObject: DataObject = None
        self.ticker = None

        if parentWidget is not None:
            bgcolor = parentWidget.palette().color(parentWidget.backgroundRole())
            self.ui.dataChart.setBackgroundByQColor( bgcolor )

        self.toolbar = NavigationToolbar(self.ui.dataChart, self)
        self.ui.toolbarLayout.addWidget( self.toolbar )

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

    def connectData(self, dataObject: DataObject, ticker):
        self.dataObject = dataObject
        self.ticker     = ticker
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

#         threads = threadlist.QThreadMeasuredList( self )
        ThreadingListType = threadlist.get_threading_list()
        threads = ThreadingListType( self )
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
        isin = self.dataObject.getStockIsinFromTicker( self.ticker )
        for i in range(0, self.ui.rangeCB.count()):
            rangeText = self.ui.rangeCB.itemText( i )
            intraSource = self.dataObject.gpwStockIntradayData.getSource( isin, rangeText )
            retList.append( intraSource )

        currentData = self.getCurrentDataSource()
        retList.append( currentData )
        return retList

    # pylint: disable=R0914
    def _updateView(self):
        self.ui.refreshPB.setEnabled( True )

        rangeText = self.ui.rangeCB.currentText()
        isin = self.dataObject.getStockIsinFromTicker( self.ticker )
        _LOGGER.debug( "updating chart data, range[%s] isin[%s]", rangeText, isin )

        intraSource = self.getIntradayDataSource()
        dataFrame = intraSource.getWorksheetData()

        self.clearData()
        if dataFrame is None:
            return

        currentSource: GpwCurrentStockData = self.getCurrentDataSource()
        currentSource.getWorksheetData()

        timeColumn   = dataFrame["t"]
        priceColumn  = dataFrame["c"]
        volumeColumn = dataFrame["v"]
#         print( "got intraday data:", priceColumn )

        price     = currentSource.getRecentValueByTicker( self.ticker )
        change    = currentSource.getRecentChangeByTicker( self.ticker )
        volumen   = volumeColumn.iloc[-1]
        refPrice  = currentSource.getReferenceValueByTicker( self.ticker )
        timestamp = timeColumn.iloc[-1]

        timeData = list(timeColumn)
        self.ui.dataChart.addPriceLine( timeData, priceColumn )

        self.ui.dataChart.addPriceSecondaryY( refPrice )

        refX = [ timeData[0], timeData[-1] ]
        refY = [ refPrice, refPrice ]
        self.ui.dataChart.addPriceLine( refX, refY, style="--" )

        transMode = self.dataObject.transactionsMatchMode()

        walletStock: TransHistory = self.dataObject.wallet[ self.ticker ]
        if walletStock is not None:
            if self.ui.showWalletCB.isChecked():
                amount, buy_unit_price = walletStock.currentTransactionsAvg( transMode )
                if amount > 0:
                    refY = [ buy_unit_price, buy_unit_price ]
                    self.ui.dataChart.addPriceLine( refX, refY, color='black', style="--" )

            if self.ui.showTransactionsLevelsCB.isChecked():
                currTransactions = walletStock.currentTransactions( transMode )
                for item in currTransactions:
                    buy_unit_price = item[1]
                    refY = [ buy_unit_price, buy_unit_price ]
                    self.ui.dataChart.addPriceLine( refX, refY, color='blue', style="--" )

            if self.ui.showTransactionsPointsCB.isChecked():
                allTransactions = walletStock.allTransactions()
                for item in allTransactions:
                    trans_time     = item[2]
                    if trans_time < timeData[0]:
                        continue
                    amount         = item[0]
                    buy_unit_price = item[1]
                    if amount > 0:
                        self.ui.dataChart.addPricePoint( trans_time, buy_unit_price, color='blue', annotation="+" )
                    else:
                        self.ui.dataChart.addPricePoint( trans_time, buy_unit_price, color='blue', annotation="-" )

        self.ui.dataChart.addVolumeLine( timeData, volumeColumn )

        recentPrice = priceColumn.iloc[-1]
        self.ui.dataChart.addVolumeSecondaryY( recentPrice )

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

    def getCurrentDataSource(self) -> GpwCurrentStockData:
        return self.dataObject.gpwCurrentData

    def deleteData(self):
        if self.dataObject:
            isin = self.dataObject.getStockIsinFromTicker( self.ticker )
            dataMap: GpwStockIntradayMap = self.dataObject.gpwStockIntradayData
            dataMap.deleteData( isin )


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
