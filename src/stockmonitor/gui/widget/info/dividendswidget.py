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

from stockmonitor.gui.widget.stocktable import StockTable, stock_background_color
from stockmonitor.gui.widget.dataframetable import TableRowColorDelegate
from stockmonitor.gui.dataobject import DataObject


_LOGGER = logging.getLogger(__name__)


class DividendsTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setShowGrid( True )
        self.setAlternatingRowColors( False )

    def _getSelectedTickers(self) -> List[str]:
        parent = self.parent()
        selectedData = self.getSelectedData( 0 )                ## name
        tickersSet = set()
        for name in selectedData:
            ticker = parent.getTickerFromName( name )
            tickersSet.add( ticker )
        return list( tickersSet )


class DividendsColorDelegate( TableRowColorDelegate ):

    def __init__(self, widget: 'DividendsWidget'):
        super().__init__()
        self.widget = widget

#     def foreground(self, index: QModelIndex ):
#         ## reimplement if needed
#         return None

    def background(self, index: QModelIndex ):
        dataRow = index.row()
        ticker = self.widget.getTicker( dataRow )

        stockColor = stock_background_color( self.widget.dataObject, ticker )
        if stockColor is not None:
            return stockColor

        todayDate = datetime.date.today()
        dateObject = self.widget.dataAccess.getLawDate( dataRow )
        if dateObject <= todayDate:
            return TableRowColorDelegate.STOCK_GRAY_BGCOLOR

        return None


class DividendsWidget( QWidget ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.dataObject: DataObject = None
        self.dataAccess = None

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.setContentsMargins( 0, 0, 0, 0 )
        self.setLayout( vlayout )
        self.dataTable = DividendsTable(self)
        vlayout.addWidget( self.dataTable )

        hlayout = QtWidgets.QHBoxLayout()
        sourceText = QtWidgets.QLabel(self)
        sourceText.setText("Source:")
        hlayout.addWidget( sourceText )

        self.sourceLabel = QtWidgets.QLabel(self)
        self.sourceLabel.setOpenExternalLinks(True)
        hlayout.addWidget( self.sourceLabel, 1 )

        vlayout.addLayout( hlayout )

    def connectData(self, dataObject: DataObject):
        self.dataObject = dataObject
        self.dataAccess = self.dataObject.gpwDividendsData

        sourceUrl = self.dataAccess.sourceLink()
        htmlText = "<a href=\"%s\">%s</a>" % (sourceUrl, sourceUrl)
        self.sourceLabel.setText( htmlText )

        colorDecorator = DividendsColorDelegate( self )
        self.dataTable.setColorDelegate( colorDecorator )

        self.dataTable.connectData( self.dataObject )

    def refreshData(self):
        dataFrame = self.dataAccess.getWorksheet()
        self.dataTable.setData( dataFrame )

    def getTicker(self, dataRow):
        stockName = self.dataAccess.getStockName( dataRow )
        ticker = self.dataObject.getTickerFromName( stockName )
        return ticker

    def getTickerFromName(self, stockName):
        return self.dataObject.getTickerFromName( stockName )
