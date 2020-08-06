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
import copy

from typing import Dict

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtWidgets import QTableView, QTableWidgetItem, QDialog
from PyQt5.QtWidgets import QMenu
from PyQt5.QtGui import QCursor

from pandas import DataFrame

from .. import uiloader
from stockmonitor.dataaccess.gpwdata import GpwCurrentData
from stockmonitor.gui import guistate


_LOGGER = logging.getLogger(__name__)


class TableSettings():

    def __init__(self):
        self.headersTexts: Dict[ int, str ]    = dict()
        self.columnsVisible: Dict[ int, bool ] = dict()

    def getText(self, col):
        return self.headersTexts.get( col, None )

    def isVisible(self, col):
        return self.columnsVisible.get( col, None )

    def setHeaderText(self, col, text):
        self.headersTexts[ col ] = text

    def setColumnVisible(self, col, show):
        self.columnsVisible[ col ] = show


UiTargetClass, QtBaseClass = uiloader.load_ui_from_module_path( "widget/tablesettingsdialog" )


class TableSettingsDialog(QtBaseClass):           # type: ignore

    setHeader  = pyqtSignal( int, str )
    showColumn = pyqtSignal( int, bool )

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        table = self.ui.columnsTable
        table.cellChanged.connect( self.tableCellChanged )

    def connectTable( self, widget: 'StockTable' ):
        self.setHeader.connect( widget.setHeaderText )
        self.showColumn.connect( widget.setColumnVisible )

    def setData(self, tableSettings, rawData: DataFrame ):
        table = self.ui.columnsTable

        headerValues = rawData.columns.values
        colsNum = rawData.shape[1]

        table.setRowCount( colsNum )

        if tableSettings is None:
            tableSettings = TableSettings()

        for i in range(0, colsNum):
            headerText  = headerValues[i][0]
            dataExample = rawData.iloc[0, i]

            ## display header
            dataItem = QTableWidgetItem()
            checkedState = Qt.Checked
            colVisible = tableSettings.isVisible( i )
            if colVisible is not None and colVisible is False:
                checkedState = Qt.Unchecked
            dataItem.setCheckState( checkedState )
            userText = tableSettings.getText( i )
            if userText is None:
                userText = headerText
            dataItem.setData( Qt.DisplayRole, userText )
            table.setItem( i, 0, dataItem )

            ## data header
            dataItem = QTableWidgetItem()
            dataItem.setFlags( dataItem.flags() ^ Qt.ItemIsEditable )
            dataItem.setData( Qt.DisplayRole, headerText )
            table.setItem( i, 1, dataItem )

            ## data preview
            dataItem = QTableWidgetItem()
            dataItem.setFlags( dataItem.flags() ^ Qt.ItemIsEditable )
            dataItem.setData( Qt.DisplayRole, dataExample )
            table.setItem( i, 2, dataItem )

        table.resizeColumnsToContents()
        table.update()

    def tableCellChanged(self, row, col):
        if col != 0:
            return
        table = self.ui.columnsTable
        tableItem = table.item( row, col )
        if tableItem is None:
            return
        headerText = tableItem.text()
        self.setHeader.emit( row, headerText )
        showValue = tableItem.checkState() != Qt.Unchecked
        self.showColumn.emit( row, showValue )


## =========================================================


class PandasModel( QAbstractTableModel ):

    def __init__(self, data: DataFrame):
        super().__init__()
        self._data: DataFrame = data
        self.customHeader: Dict[ object, str ] = dict()

    # pylint: disable=W0613
    def rowCount(self, parent=None):
        return self._data.shape[0]

    # pylint: disable=W0613
    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            key = (section, orientation, role)
            headerValue = self.customHeader.get( key, None )
            if headerValue is not None:
                return headerValue
            colName = self._data.columns[section]
            return colName[0]
        return None

    def setHeaderData(self, section, orientation, value, role=Qt.DisplayRole):
        # return super().setHeaderData( section, orientation, value, role )
        key = (section, orientation, role)
        self.customHeader[ key ] = value
        self.headerDataChanged.emit( orientation, section, section )
        return True

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None


class StockTable( QTableView ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self._data = None
        self.tableSettings = TableSettings()

    def setData(self, rawData: DataFrame ):
        self._data = rawData
        self.setModel( PandasModel( rawData ) )
        self._applySettings()

    def showColumnsConfiguration(self):
        if self._data is None:
            return
        oldSettings = copy.deepcopy( self.tableSettings )
        dialog = TableSettingsDialog( self )
        dialog.setData( self.tableSettings, self._data )
        dialog.connectTable( self )
        dialogCode = dialog.exec_()
        if dialogCode == QDialog.Rejected:
            ##restore old settings
            self.tableSettings = oldSettings
            self._applySettings()

    def refreshData(self, forceRefresh=True):
        dataAccess = GpwCurrentData()
        dataframe = dataAccess.getWorksheet( forceRefresh )
        self.setData( dataframe )

    def setHeaderText(self, col, text):
        self.tableSettings.setHeaderText( col, text )
        self.model().setHeaderData( col, Qt.Horizontal, text )

    def setColumnVisible(self, col, visible):
        self.tableSettings.setColumnVisible( col, visible )
        self.setColumnHidden( col, not visible )

    def loadSettings(self, settings):
        settings.beginGroup( guistate.get_widget_key(self, "tablesettings") )
 
        textDict = settings.value("headersTexts", None, type=dict)
        if textDict is not None:
            self.tableSettings.headersTexts = textDict
            
        visDict = settings.value("columnsVisible", None, type=dict)
        if visDict is not None:
            self.tableSettings.columnsVisible = visDict
 
        settings.endGroup()
        
        self._applySettings()

    def saveSettings(self, settings):
        settings.beginGroup( guistate.get_widget_key(self, "tablesettings") )
        settings.setValue("headersTexts", self.tableSettings.headersTexts )
        settings.setValue("columnsVisible", self.tableSettings.columnsVisible )
        settings.endGroup()

    def _applySettings(self):
        tableModel = self.model()
        tableModel.customHeader.clear()
        for col, text in self.tableSettings.headersTexts.items():
            tableModel.setHeaderData( col, Qt.Horizontal, text )

        colsCount = tableModel.columnCount()
        for col in range(0, colsCount):
            self.showColumn( col )
        for col, show in self.tableSettings.columnsVisible.items():
            self.setColumnHidden( col, not show )

    def contextMenuEvent( self, event ):
        contextMenu         = QMenu(self)
        refreshAction       = contextMenu.addAction("Refresh data")
        configColumnsAction = contextMenu.addAction("Configure columns")

        if self._data is None:
            configColumnsAction.setEnabled( False )
        
        globalPos = QCursor.pos()
        action = contextMenu.exec_( globalPos )

        if action == refreshAction:
            self.refreshData()
        elif action == configColumnsAction:
            self.showColumnsConfiguration()
