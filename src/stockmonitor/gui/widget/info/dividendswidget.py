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
from typing import List

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

    def _getSelectedCodes(self) -> List[str]:
        parent = self.parent()
        selectedRows = self.getSelectedRows()
        favCodes = set()
        for dataRow in selectedRows:
            code = parent.getStockCode( dataRow )
            favCodes.add( code )
        favList = list(favCodes)
        return favList


class DividendsColorDelegate( TableRowColorDelegate ):

    def __init__(self, widget: 'DividendsWidget'):
        self.widget = widget

#     def foreground(self, index: QModelIndex ):
#         ## reimplement if needed
#         return None

    def background(self, index: QModelIndex ):
        dataRow = index.row()
        stockCode = self.widget.getStockCode( dataRow )
        allFavs = self.widget.dataObject.favs.getFavsAll()
        if stockCode in allFavs:
            return TableRowColorDelegate.STOCK_FAV_BGCOLOR
        todayDate = datetime.date.today()
        dateObject = self.widget.dataAccess.getLawDate( dataRow )
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

        self.dataObject: DataObject = None
        self.dataAccess = DividendsCalendarData()
        self.refreshData( False )

    def connectData(self, dataObject: DataObject):
        self.dataObject = dataObject

        colorDecorator = DividendsColorDelegate( self )
        self.dataTable.setColorDelegate( colorDecorator )

        self.dataTable.connectData( self.dataObject )

    def setDataAccess(self, dataAccess: DividendsCalendarData):
        self.dataAccess = dataAccess
        self.refreshData( False )

    def refreshData(self, forceRefresh=True):
        if forceRefresh:
            self.dataAccess.refreshData()
        dataFrame = self.dataAccess.getWorksheet()
        self.dataTable.setData( dataFrame )

    def getStockCode(self, dataRow):
        stockName = self.dataAccess.getStockName( dataRow )
        stockCode = self.dataObject.getStockCodeFromName( stockName )
        return stockCode
