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

from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QDesktopServices

from stockmonitor.dataaccess import tmp_dir
from stockmonitor.dataaccess.stockanalysis import StockAnalysis
from stockmonitor.dataaccess.activityanalysis import GpwCurrentIntradayProvider,\
    ActivityAnalysis, MetaStockIntradayProvider
from stockmonitor.gui import threadlist
from stockmonitor.gui.utils import set_label_url

from ... import uiloader


UiTargetClass, QtBaseClass = uiloader.load_ui_from_module_path( __file__ )


_LOGGER = logging.getLogger(__name__)


class ActivityWidget(QtBaseClass):           # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.recentOutput = None

        toDate = datetime.date.today() - datetime.timedelta( days=1 )
        self.ui.fromDE.setDate( toDate )
        self.ui.toDE.setDate( toDate )

#         toDate   = datetime.date.today() - datetime.timedelta( days=1 )
#         fromDate = toDate - datetime.timedelta( days=7 )
#
#         self.ui.fromDE.setDate( fromDate )
#         self.ui.toDE.setDate( toDate )

        self.ui.openPB.setEnabled( False )

        analysis = StockAnalysis()
        self.ui.sourceLabel.setTextInteractionFlags( Qt.TextBrowserInteraction )
        self.ui.sourceLabel.setOpenExternalLinks(True)
        set_label_url( self.ui.sourceLabel, analysis.sourceLink() )

        self.ui.calculatePB.clicked.connect( self.calculate )
        self.ui.openPB.clicked.connect( self.openResults )

        self.ui.limitResultsCB.currentIndexChanged.connect( self.ui.dataTable.limitResults )

        self.ui.todayDataRB.click()

    def connectData(self, dataObject):
        self.ui.dataTable.connectData( dataObject )

    def calculate(self):
        if self.ui.todayDataRB.isChecked():
            _LOGGER.warning("calculating based on current intraday")
            threadlist.QThreadMeasuredList.calculate( self, self._calculateCurr )
        elif self.ui.rangeDataRB.isChecked():
            _LOGGER.warning("calculating based on metastock intraday")
            threadlist.QThreadMeasuredList.calculate( self, self._calculatePrev )
        else:
            _LOGGER.warning("unknown state")

    def _calculateCurr(self):
        self.ui.calculatePB.setEnabled( False )
        self.ui.openPB.setEnabled( False )
        self.ui.dataTable.clear()

        thresh = self.ui.threshSB.value()

        dataProvider = GpwCurrentIntradayProvider()
        analysis = ActivityAnalysis( dataProvider )
        today = datetime.datetime.now().date()
        self.recentOutput = tmp_dir + "out/output_activity.csv"
        resultData = analysis.calcActivity( today, today, thresh, self.recentOutput, True )

        self.ui.dataTable.setData( resultData )

        self.ui.calculatePB.setEnabled( True )
        self.ui.openPB.setEnabled( True )

    def _calculatePrev(self):
        self.ui.calculatePB.setEnabled( False )
        self.ui.openPB.setEnabled( False )
        self.ui.dataTable.clear()

        fromDate = self.ui.fromDE.date().toPyDate()
        toDate   = self.ui.toDE.date().toPyDate()
        thresh   = self.ui.threshSB.value()

        dataProvider = MetaStockIntradayProvider()
        analysis = ActivityAnalysis( dataProvider )
        self.recentOutput = tmp_dir + "out/output_activity.csv"
        resultData = analysis.calcActivity( fromDate, toDate, thresh, self.recentOutput )

        self.ui.dataTable.setData( resultData )

        self.ui.calculatePB.setEnabled( True )
        self.ui.openPB.setEnabled( True )

    def openResults(self):
        url = QUrl.fromLocalFile( self.recentOutput )
        QDesktopServices.openUrl( url )
