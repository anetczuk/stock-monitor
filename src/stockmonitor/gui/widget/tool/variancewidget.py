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

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from stockmonitor.dataaccess import stockdata
from stockmonitor.dataaccess.stockdata import StockAnalysis

from ... import uiloader


UiTargetClass, QtBaseClass = uiloader.load_ui_from_module_path( __file__ )


_LOGGER = logging.getLogger(__name__)


class VarianceWidget(QtBaseClass):           # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.recentOutput = None

        toDate   = datetime.date.today()
        fromDate = toDate - datetime.timedelta( days=7 )

        self.ui.fromDE.setDate( fromDate )
        self.ui.toDE.setDate( toDate )

        self.ui.openPB.setEnabled( False )

        self.ui.calculatePB.clicked.connect( self.calculate )
        self.ui.openPB.clicked.connect( self.openResults )

    def calculate(self):
        fromDate = self.ui.fromDE.date().toPyDate()
        toDate   = self.ui.toDE.date().toPyDate()

        analysis = StockAnalysis()

        self.recentOutput = stockdata.tmp_dir + "out/output_variance.csv"
        resultData = analysis.calcVariance( fromDate, toDate, self.recentOutput )
        self.ui.stockTable.setData( resultData )
        self.ui.openPB.setEnabled( True )

    def openResults(self):
        url = QUrl.fromLocalFile( self.recentOutput )
        QDesktopServices.openUrl( url )
