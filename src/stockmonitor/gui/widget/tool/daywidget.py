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
from enum import unique, Enum

from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QDesktopServices

from stockdataaccess.dataaccess import tmp_dir

from stockmonitor.analysis.stockanalysis import StockAnalysis
from stockmonitor.gui.utils import set_label_url

from ... import uiloader


UiTargetClass, QtBaseClass = uiloader.load_ui_from_module_path( __file__ )


_LOGGER = logging.getLogger(__name__)


@unique
class DaysDataType(Enum):
    MONDAY = ()
    FRIDAY = ()
    WEEKEND = ()

    def __new__(cls):
        value = len(cls.__members__)  # note no + 1
        obj = object.__new__(cls)
        # pylint: disable=W0212
        obj._value_ = value
        return obj


class DayWidget(QtBaseClass):           # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.recentOutput = None

        self.ui.openPB.setEnabled( False )

        for value in DaysDataType:
            self.ui.fieldCB.addItem( value.name, value )

        analysis = StockAnalysis()
        self.ui.sourceLabel.setTextInteractionFlags( Qt.TextBrowserInteraction )
        self.ui.sourceLabel.setOpenExternalLinks(True)
        set_label_url( self.ui.sourceLabel, analysis.sourceLink() )

        self.ui.calculatePB.clicked.connect( self.calculate )
        self.ui.openPB.clicked.connect( self.openResults )

        self.ui.limitResultsCB.currentIndexChanged.connect( self.ui.dataTable.limitResults )

    def connectData(self, dataObject):
        self.ui.dataTable.connectData( dataObject )

    def calculate(self):
        weeksNum   = self.ui.numWeeksSB.value()
        fieldIndex = self.ui.fieldCB.currentIndex()
        fieldValue = self.ui.fieldCB.itemData( fieldIndex )
        self.recentOutput = tmp_dir + "out/output_day.csv"

        resultData = None

        analysis = StockAnalysis()
        if fieldValue == DaysDataType.MONDAY:
            resultData = analysis.calcMonday( weeksNum, outFilePath=self.recentOutput )
        elif fieldValue == DaysDataType.FRIDAY:
            resultData = analysis.calcFriday( weeksNum, outFilePath=self.recentOutput )
        elif fieldValue == DaysDataType.WEEKEND:
            resultData = analysis.calcWeekend( weeksNum, outFilePath=self.recentOutput )

        self.ui.dataTable.setData( resultData )
        self.ui.openPB.setEnabled( True )

    def openResults(self):
        url = QUrl.fromLocalFile( self.recentOutput )
        QDesktopServices.openUrl( url )
