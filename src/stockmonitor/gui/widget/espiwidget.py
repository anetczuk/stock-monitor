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

from stockmonitor.gui.widget.stocktable import stock_background_color

from .. import uiloader


_LOGGER = logging.getLogger(__name__)


DetailsUiClass, DetailsBaseClass = uiloader.load_ui_from_module_path( "widget/espidetails" )


class ESPIDetails( DetailsBaseClass ):                      # type: ignore

    def __init__(self, dataRow, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = DetailsUiClass()
        self.ui.setupUi(self)

        self.ui.company.setOpenExternalLinks(True)
        self.ui.company.setUrl( dataRow["url"], dataRow["name"] )
        self.ui.date.setText( str( dataRow["date"] ) )
        self.ui.title.setText( dataRow["title"] )


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class ESPIListWidget( QtBaseClass ):                        # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.dataObject = None

    def connectData(self, dataObject):
        self.dataObject = dataObject
        self.dataObject.stockDataChanged.connect( self.updateView )
        self.dataObject.favsChanged.connect( self.updateView )
        self.dataObject.walletDataChanged.connect( self.updateView )

    def updateView(self):
        self.ui.espiList.clear()
        if self.dataObject is None:
            _LOGGER.warning("unable to update view")
            return
        espiData = self.dataObject.gpwESPIData
        if espiData is None:
            _LOGGER.info("no data to view")
            return
        dataFrame = espiData.getWorksheet()
        if dataFrame is None:
            _LOGGER.info("no data to view")
            return

        _LOGGER.info("updating view")
        for _, row in dataFrame.iterrows():
            self.addItem( row )

    def addItem(self, row):
        item = QtWidgets.QListWidgetItem()
        details = ESPIDetails( row, self )
        item.setSizeHint( details.sizeHint() )

        ticker = self.dataObject.getTickerFromIsin( row["isin"] )
        bgColor = stock_background_color( self.dataObject, ticker )
        if bgColor is not None:
            item.setBackground( bgColor )

        self.ui.espiList.addItem( item )
        self.ui.espiList.setItemWidget( item, details )
