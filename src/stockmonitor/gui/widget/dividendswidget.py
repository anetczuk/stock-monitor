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

from PyQt5 import QtWidgets
from PyQt5.QtCore import QModelIndex
from PyQt5.QtWidgets import QWidget

from stockmonitor.gui.widget.stocktable import StockTable
from stockmonitor.dataaccess.dividendsdata import DividendsCalendarData
from stockmonitor.gui.widget.dataframetable import TableRowColorDelegate
from stockmonitor.gui.dataobject import DataObject


_LOGGER = logging.getLogger(__name__)


class DividendsTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setShowGrid( True )
        self.setAlternatingRowColors( False )


class DividendsColorDelegate( TableRowColorDelegate ):

    def __init__(self, dataAccess: DividendsCalendarData, dataObject: DataObject):
        self.dataAccess = dataAccess
        self.dataObject = dataObject

#     def foreground(self, index: QModelIndex ):
#         ## reimplement if needed
#         return None

    def background(self, index: QModelIndex ):
        dataRow = index.row()
        stockName = self.dataAccess.getStockName( dataRow )
        stockCode = self.dataObject.getStockCodeFromName( stockName )
        allFavs = self.dataObject.favs.getFavsAll()
        if stockCode in allFavs:
            return TableRowColorDelegate.STOCK_FAV_BGCOLOR
        todayDate = datetime.date.today()
        dateObject = self.dataAccess.getLawDate( dataRow )
        if dateObject <= todayDate:
            return TableRowColorDelegate.STOCK_GRAY_BGCOLOR
        return None


class DividendsWidget( QWidget ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.setContentsMargins( 0, 0, 0, 0 )
        self.setLayout( vlayout )
        self.dataTable = DividendsTable(self)

        vlayout.addWidget( self.dataTable )

        self.dataObject = None
        self.dataAccess = DividendsCalendarData()
        self.refreshData( False )

    def connectData(self, dataObject):
        self.dataObject = dataObject

        colorDecorator = DividendsColorDelegate( self.dataAccess, self.dataObject )
        self.dataTable.setColorDelegate( colorDecorator )

    def setDataAccess(self, dataAccess: DividendsCalendarData):
        self.dataAccess = dataAccess
        self.refreshData( False )

    def refreshData(self, forceRefresh=True):
        if forceRefresh:
            self.dataAccess.refreshData()
        dataFrame = self.dataAccess.getWorksheet()
        self.dataTable.setData( dataFrame )
