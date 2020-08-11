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
import re

from typing import Dict

from pandas import DataFrame

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtWidgets import QTableView, QTableWidgetItem
from PyQt5.QtWidgets import QMenu
from PyQt5.QtGui import QCursor

from .. import uiloader
from .. import guistate


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

        self.parentTable = None
        self.oldSettings = None

        table = self.ui.columnsTable
        table.cellChanged.connect( self.tableCellChanged )
        self.rejected.connect( self.settingsRejected )

    def connectTable( self, parentTable: 'StockTable' ):
        self.parentTable = parentTable
        self.oldSettings = copy.deepcopy( parentTable.tableSettings )
        self.setHeader.connect( parentTable.setHeaderText )
        self.showColumn.connect( parentTable.setColumnVisible )

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

    def settingsRejected(self):
        ##restore old settings
        self.parentTable.setTableSettings( self.oldSettings )


## =========================================================


class PandasModel( QAbstractTableModel ):

    def __init__(self, data: DataFrame):
        super().__init__()
        self._data: DataFrame = data
        self.customHeader: Dict[ object, str ] = dict()

    def setContent(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    # pylint: disable=W0613
    def rowCount(self, parent=None):
        if self._data is None:
            return 0
        return self._data.shape[0]

    # pylint: disable=W0613
    def columnCount(self, parnet=None):
        if self._data is None:
            return 0
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
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        if role == Qt.TextAlignmentRole:
            return Qt.AlignHCenter | Qt.AlignVCenter
        return None


def contains_string( data ):
    if data == '-':
        return True
    if re.search('[a-zA-Z:]', data):
        return True
    return False


def convert_float( data ):
    value = data.strip()
    value = value.replace(',', '.')
    value = re.sub(r'\s+', '', value)       ## remove whitespaces
    return float(value)


def convert_int( data ):
    value = data.strip()
    value = re.sub(r'\s+', '', value)       ## remove whitespaces
    return int(value)


class TaskSortFilterProxyModel( QtCore.QSortFilterProxyModel ):

    def lessThan(self, left: QModelIndex, right: QModelIndex):
        leftData  = self.sourceModel().data(left, QtCore.Qt.DisplayRole)
        rightData = self.sourceModel().data(right, QtCore.Qt.DisplayRole)
        leftData, rightData  = self.convertType( leftData, rightData )
        return leftData < rightData

    def convertType(self, leftData, rightData):
        if contains_string(leftData) or contains_string(rightData):
            return (leftData, rightData)

        try:
            left  = convert_float(leftData)
            right = convert_float(rightData)
            return (left, right)
        except ValueError:
            pass
        try:
            left  = convert_int(leftData)
            right = convert_int(rightData)
            return (left, right)
        except ValueError:
            pass

        #print("unable to detect type:", ascii(leftData), ascii(rightData) )
        return (leftData, rightData)


class StockTable( QTableView ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self._data = None
        self.tableSettings = TableSettings()

        self.setSortingEnabled( True )

        header = self.horizontalHeader()
        header.setDefaultAlignment( Qt.AlignCenter )
        header.setHighlightSections( False )
        header.setStretchLastSection( True )

        self.pandaModel = PandasModel( None )
        proxyModel = TaskSortFilterProxyModel(self)
        proxyModel.setSourceModel( self.pandaModel )
        self.setModel( proxyModel )

        self.setData( DataFrame() )

    def setData(self, rawData: DataFrame ):
        self._data = rawData
        self.pandaModel.setContent( rawData )
        self._applySettings()

    def showColumnsConfiguration(self):
        if self._data is None:
            return
        dialog = TableSettingsDialog( self )
        dialog.setData( self.tableSettings, self._data )
        dialog.connectTable( self )
        dialog.show()

    def setHeaderText(self, col, text):
        self.tableSettings.setHeaderText( col, text )
        self.pandaModel.setHeaderData( col, Qt.Horizontal, text )

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

    def setTableSettings(self, settings):
        self.tableSettings = settings
        self._applySettings()

    def _applySettings(self):
        tableModel = self.pandaModel
        tableModel.customHeader.clear()
        for col, text in self.tableSettings.headersTexts.items():
            tableModel.setHeaderData( col, Qt.Horizontal, text )

        colsCount = tableModel.columnCount()
        for col in range(0, colsCount):
            self.showColumn( col )
        for col, show in self.tableSettings.columnsVisible.items():
            self.setColumnHidden( col, not show )

    def contextMenuEvent( self, _ ):
        contextMenu         = QMenu(self)
        configColumnsAction = contextMenu.addAction("Configure columns")

        if self._data is None:
            configColumnsAction.setEnabled( False )

        globalPos = QCursor.pos()
        action = contextMenu.exec_( globalPos )

        if action == configColumnsAction:
            self.showColumnsConfiguration()


## ====================================================================


class StockFullTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.dataObject = None

    def connectData(self, dataObject):
        self.dataObject = dataObject
        self.dataObject.stockDataChanged.connect( self.updateData )
        self.updateData()

    def updateData(self):
        dataAccess = self.dataObject.currentStockData
        dataframe = dataAccess.getWorksheet( False )
        self.setData( dataframe )

    def contextMenuEvent( self, _ ):
        contextMenu         = QMenu(self)
        refreshAction       = contextMenu.addAction("Refresh data")
        configColumnsAction = contextMenu.addAction("Configure columns")

        favsActions = []
        if self.dataObject is not None:
            favSubMenu          = contextMenu.addMenu("Add to favs")
            favGroupsList = self.dataObject.favs.favGroupsList()
            if not favGroupsList:
                favSubMenu.setEnabled( False )
            else:
                for favGroup in favGroupsList:
                    favAction = favSubMenu.addAction( favGroup )
                    favAction.setData( favGroup )
                    favsActions.append( favAction )

        if self._data is None:
            configColumnsAction.setEnabled( False )

        globalPos = QCursor.pos()
        action = contextMenu.exec_( globalPos )

        if action == refreshAction:
            self.dataObject.refreshStockData()
        elif action == configColumnsAction:
            self.showColumnsConfiguration()
        elif action in favsActions:
            favGroup = action.data()
            dataAccess = self.dataObject.currentStockData
            selection = self.selectionModel()
            indexes = selection.selectedIndexes()
            favCodes = set()
            for ind in indexes:
                sourceIndex = self.model().mapToSource( ind )
                dataRow = sourceIndex.row()
                code = dataAccess.getShortField( dataRow )
                favCodes.add( code )
            favList = list(favCodes)
            self.dataObject.addFav( favGroup, favList )


## ====================================================================


class StockFavsTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.dataObject = None
        self.favGroup = None

    def connectData(self, dataObject, favGroup):
        self.dataObject = dataObject
        self.favGroup = favGroup
        if self.dataObject is None:
            return
        self.dataObject.stockDataChanged.connect( self.updateData )
        self.updateData()

    def updateData(self):
        dataframe = self.dataObject.getFavStock( self.favGroup )
        self.setData( dataframe )

    def contextMenuEvent( self, _ ):
        contextMenu         = QMenu(self)
        refreshAction       = contextMenu.addAction("Refresh data")
        configColumnsAction = contextMenu.addAction("Configure columns")
        remFavAction        = contextMenu.addAction("Remove fav")

        globalPos = QCursor.pos()
        action = contextMenu.exec_( globalPos )

        if action == refreshAction:
            self.dataObject.refreshStockData()
        elif action == configColumnsAction:
            self.showColumnsConfiguration()
        elif action == remFavAction:
            dataAccess = self.dataObject.currentStockData
            selection = self.selectionModel()
            indexes = selection.selectedIndexes()
            favCodes = set()
            for ind in indexes:
                sourceIndex = self.model().mapToSource( ind )
                dataRow = sourceIndex.row()
                code = dataAccess.getShortFieldFromData( self._data, dataRow )
                favCodes.add( code )
            favList = list(favCodes)
            self.dataObject.deleteFav( self.favGroup, favList )
