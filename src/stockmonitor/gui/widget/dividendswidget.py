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

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget

from stockmonitor.gui.widget.stocktable import StockTable
from stockmonitor.dataaccess.dividendsdata import DividendsCalendarData


_LOGGER = logging.getLogger(__name__)


class DividendsTable( StockTable ):

    pass


class DividendsWidget( QWidget ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.setContentsMargins( 0, 0, 0, 0 )
        self.setLayout( vlayout )
        self.dataTable = DividendsTable(self)

        vlayout.addWidget( self.dataTable )

        self.dataAccess: DividendsCalendarData = None

    def setDataAccess(self, dataAccess: DividendsCalendarData):
        self.dataAccess = dataAccess
        self.refreshData( False )

    def refreshData(self, forceRefresh=True):
        if forceRefresh:
            self.dataAccess.refreshData()
        dataFrame = self.dataAccess.getWorksheet()
        self.dataTable.setData( dataFrame )
