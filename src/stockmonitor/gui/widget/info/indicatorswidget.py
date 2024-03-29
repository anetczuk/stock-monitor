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

from stockmonitor.gui.widget.stocktable import StockTable, stock_background_color
from stockmonitor.gui.widget.dataframetable import TableRowColorDelegate
from stockmonitor.gui.dataobject import DataObject
from stockmonitor.gui.utils import set_label_url


_LOGGER = logging.getLogger(__name__)


class IndicatorsTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setShowGrid( True )
        self.setAlternatingRowColors( False )

    ## override
    def _getSelectedTickers(self) -> List[str]:
        parent = self.parent()
        selectedData = self.getSelectedData( 2 )                ## name
        tickersSet = set()
        for name in selectedData:
            ticker = parent.getTickerFromName( name )           # type: ignore
            tickersSet.add( ticker )
        return list(tickersSet)

    ## override
    def _getSelectedIsins(self) -> List[str]:
        selectedData = self.getSelectedData( 1 )                ## isin
        return list( selectedData )


class IndicatorsColorDelegate( TableRowColorDelegate ):

    def __init__(self, widget: 'IndicatorsWidget'):
        super().__init__()
        self.widget = widget

#     def foreground(self, index: QModelIndex ):
#         ## reimplement if needed
#         return None

    def background(self, index: QModelIndex ):
        dataRow = index.row()
        ticker = self.widget.getTicker( dataRow )
        return stock_background_color( self.widget.dataObject, ticker )


class IndicatorsWidget( QWidget ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.dataObject: DataObject = None
        self.dataAccess = None

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.setContentsMargins( 0, 0, 0, 0 )
        self.setLayout( vlayout )
        self.dataTable = IndicatorsTable(self)
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
        self.dataAccess = self.dataObject.gpwIndicatorsData

        set_label_url( self.sourceLabel, self.dataAccess.sourceLink() )

        colorDecorator = IndicatorsColorDelegate( self )
        self.dataTable.setColorDelegate( colorDecorator )

        self.dataTable.connectData( self.dataObject )

    def refreshData(self):
        dataFrame = self.dataAccess.getWorksheetData()
        self.dataTable.setData( dataFrame )

    def getTicker(self, dataRow):
        stockIsin = self.dataAccess.getStockIsin( dataRow )
        return self.dataObject.getTickerFromIsin( stockIsin )

    def getTickerFromName(self, stockName):
        return self.dataObject.getTickerFromName( stockName )
