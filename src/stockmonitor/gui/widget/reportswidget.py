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

from typing import List

from PyQt5 import QtWidgets
from PyQt5.QtCore import QModelIndex
from PyQt5.QtWidgets import QWidget

from stockmonitor.gui.widget.stocktable import StockTable
from stockmonitor.dataaccess.worksheetdata import WorksheetData
from stockmonitor.dataaccess.finreportscalendardata import PublishedFinRepsCalendarData, FinRepsCalendarData
from stockmonitor.gui.widget.dataframetable import TableRowColorDelegate
from stockmonitor.gui.dataobject import DataObject


_LOGGER = logging.getLogger(__name__)


class ReportsTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setShowGrid( True )
        self.setAlternatingRowColors( False )
        
    def _getSelectedCodes(self) -> List[str]:
        dataAccess = self.parent().dataAccess
        selectedRows = self.getSelectedRows()
        favCodes = set()
        for dataRow in selectedRows:
            code = dataAccess.getStockCode( dataRow )
            favCodes.add( code )
        favList = list(favCodes)
        return favList


class ReportsColorDelegate( TableRowColorDelegate ):

    def __init__(self, dataAccess, dataObject: DataObject):
        self.dataAccess = dataAccess
        self.dataObject = dataObject

#     def foreground(self, index: QModelIndex ):
#         ## reimplement if needed
#         return None

    def background(self, index: QModelIndex ):
        dataRow = index.row()
        stockCode = self.dataAccess.getStockCode( dataRow )
        allFavs = self.dataObject.favs.getFavsAll()
        if stockCode in allFavs:
            return TableRowColorDelegate.STOCK_FAV_BGCOLOR
        return None


class ReportsWidget( QWidget ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.setContentsMargins( 0, 0, 0, 0 )
        self.setLayout( vlayout )
        self.dataTable = ReportsTable(self)

        vlayout.addWidget( self.dataTable )

        self.dataObject = None
        self.dataAccess = FinRepsCalendarData()
        self.refreshData( False )

    def connectData(self, dataObject: DataObject):
        self.dataObject = dataObject

        colorDecorator = ReportsColorDelegate( self.dataAccess, self.dataObject )
        self.dataTable.setColorDelegate( colorDecorator )
        
        self.dataTable.connectData( self.dataObject )

    def setDataAccess(self, dataAccess: WorksheetData):
        self.dataAccess = dataAccess
        self.refreshData( False )

    def refreshData(self, forceRefresh=True):
        if forceRefresh:
            self.dataAccess.refreshData()
        dataFrame = self.dataAccess.getWorksheet()
        self.dataTable.setData( dataFrame )


class PublishedReportsWidget( QWidget ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.setContentsMargins( 0, 0, 0, 0 )
        self.setLayout( vlayout )
        self.dataTable = ReportsTable(self)

        vlayout.addWidget( self.dataTable )

        self.dataObject = None
        self.dataAccess = PublishedFinRepsCalendarData()
        self.refreshData( False )

    def connectData(self, dataObject):
        self.dataObject = dataObject

        colorDecorator = ReportsColorDelegate( self.dataAccess, self.dataObject )
        self.dataTable.setColorDelegate( colorDecorator )
        
        self.dataTable.connectData( self.dataObject )

    def setDataAccess(self, dataAccess: WorksheetData):
        self.dataAccess = dataAccess
        self.refreshData( False )

    def refreshData(self, forceRefresh=True):
        if forceRefresh:
            self.dataAccess.refreshData()
        dataFrame = self.dataAccess.getWorksheet()
        self.dataTable.setData( dataFrame )
