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
from stockmonitor.gui.dataobject import DataObject
from stockmonitor.gui.widget.dataframetable import TableRowColorDelegate
from stockmonitor.gui.utils import set_label_url


_LOGGER = logging.getLogger(__name__)


class ShortSellingsTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setShowGrid( True )
        self.setAlternatingRowColors( False )

    ## override
    def _getSelectedTickers(self) -> List[str]:
        isinSet = self.getSelectedData( 2 )
        retList = []
        for isin in isinSet:
            ticker = self.dataObject.getTickerFromIsin( isin )
            retList.append( ticker )
        return retList

    ## override
    def _getSelectedIsins(self) -> List[str]:
        isinSet = self.getSelectedData( 2 )
        return list( isinSet )


class ShortSellingsColorDelegate( TableRowColorDelegate ):

    def __init__(self, dataAccess, dataObject: DataObject):
        super().__init__()
        self.dataAccess = dataAccess
        self.dataObject = dataObject

#     def foreground(self, index: QModelIndex ):
#         ## reimplement if needed
#         return None

    def background(self, index: QModelIndex ):
        dataRow = index.row()
        isin = self.dataAccess.getISIN( dataRow )
        ticker = self.dataObject.getTickerFromIsin( isin )
        return stock_background_color( self.dataObject, ticker )


class ShortSellingsWidget( QWidget ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.dataObject  = None
        self.currentData = None
        self.historyData = None

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.setContentsMargins( 0, 0, 0, 0 )
        self.setLayout( vlayout )

        ## label row
        sourceText = QtWidgets.QLabel(self)
        sourceText.setText("Current short sellings:")
        vlayout.addWidget( sourceText )

        ## current shorts row
        self.currentShortsTable = ShortSellingsTable(self)
        self.currentShortsTable.setObjectName("currentshortstable")
        vlayout.addWidget( self.currentShortsTable )

        ## label row
        sourceText = QtWidgets.QLabel(self)
        sourceText.setText("History of short sellings:")
        vlayout.addWidget( sourceText )

        ## history shorts row
        self.historyShortsTable = ShortSellingsTable(self)
        self.historyShortsTable.setObjectName("historyshortstable")
        vlayout.addWidget( self.historyShortsTable )

        ## source info row
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
        self.currentData = self.dataObject.gpwCurrentShortSellingsData
        self.historyData = self.dataObject.gpwHistoryShortSellingsData

        colorDecorator = ShortSellingsColorDelegate( self.currentData, self.dataObject )
        self.currentShortsTable.setColorDelegate( colorDecorator )
        self.currentShortsTable.connectData( self.dataObject )

        colorDecorator = ShortSellingsColorDelegate( self.historyData, self.dataObject )
        self.historyShortsTable.setColorDelegate( colorDecorator )
        self.historyShortsTable.connectData( self.dataObject )

        set_label_url( self.sourceLabel, self.currentData.sourceLink() )

    def refreshData(self):
        currentFrame = self.currentData.getWorksheet()
        self.currentShortsTable.setData( currentFrame )

        historyFrame = self.historyData.getWorksheet()
        self.historyShortsTable.setData( historyFrame )
