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
import io
import csv
import math

from typing import Dict

from urllib.parse import urlparse
from pandas import DataFrame

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QModelIndex, QUrl
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtWidgets import QTableView, QTableWidgetItem
from PyQt5.QtWidgets import QMenu
from PyQt5.QtGui import QCursor
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtGui import QColor

## workaround for mypy type errors
from PyQt5.QtCore import Qt

from .. import uiloader
from .. import guistate


QtChecked = Qt.Checked                          # type: ignore
QtUnchecked = Qt.Unchecked                      # type: ignore
QtDisplayRole = Qt.DisplayRole                  # type: ignore
QtUserRole = Qt.UserRole                        # type: ignore
QtTextAlignmentRole = Qt.TextAlignmentRole      # type: ignore
QtForegroundRole = Qt.ForegroundRole            # type: ignore
QtBackgroundRole = Qt.BackgroundRole            # type: ignore
QtAlignHCenter = Qt.AlignHCenter                # type: ignore
QtAlignVCenter = Qt.AlignVCenter                # type: ignore
QtItemIsEditable = Qt.ItemIsEditable            # type: ignore


_LOGGER = logging.getLogger(__name__)


# pylint: disable=C0301
TableSettingsDialogUiClass, TableSettingsDialogBaseClass = uiloader.load_ui_from_module_path( "widget/tablesettingsdialog" )


def is_nan( value ):
    try:
        return math.isnan( value )
    except TypeError:
        return False


def is_invalid_number( value ):
    if value is None:
        return True
    if value in ("-", "--", "x"):
        return True
    if is_nan( value ):
        return True
    return False


class TableSettingsDialog(TableSettingsDialogBaseClass):           # type: ignore

    setHeader  = pyqtSignal( int, str )
    showColumn = pyqtSignal( int, bool )

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = TableSettingsDialogUiClass()
        self.ui.setupUi(self)

        self.parentTable: 'DataFrameTable'  = None

        self.oldHeaders = None
        self.oldColumns = None

        table = self.ui.columnsTable
        table.cellChanged.connect( self.tableCellChanged )
        self.rejected.connect( self.settingsRejected )

    def connectTable( self, parentTable: 'DataFrameTable' ):
        self.parentTable = parentTable

        self.oldHeaders = copy.deepcopy( parentTable.headersText )
        self.oldColumns = copy.deepcopy( parentTable.columnsVisible )

        self.setHeader.connect( parentTable.setHeaderText )
        self.showColumn.connect( parentTable.setColumnVisible )
        self.accepted.connect( parentTable.settingsAccepted )
        self.rejected.connect( parentTable.settingsRejected )

        self.ui.resizeColumnsPB.clicked.connect( parentTable.resizeColumnsToContents )

#         self.adjustSize()

    def setData(self, rawData: DataFrame ):
        table = self.ui.columnsTable
        headerValues = rawData.columns.values
        rowsNum = rawData.shape[0]
        colsNum = rawData.shape[1]

        table.setRowCount( colsNum )

        for i in range(0, colsNum):
            headerVal  = headerValues[i]
            headerText = ""
            if isinstance(headerVal, tuple):
                headerText = headerVal[0]
            else:
                headerText = headerVal
            dataExample = None
            if rowsNum > 0:
                dataExample = rawData.iloc[0, i]

            ## display header
            dataItem = QTableWidgetItem()
            checkedState = QtChecked
            colVisible = self.isColumnVisible( i )
            if colVisible is not None and colVisible is False:
                checkedState = QtUnchecked
            dataItem.setCheckState( checkedState )
            userText = self.getHeaderText( i )
            if userText is None:
                userText = headerText
            dataItem.setData( QtDisplayRole, userText )
            table.setItem( i, 0, dataItem )

            ## data header
            dataItem = QTableWidgetItem()
            dataItem.setFlags( dataItem.flags() ^ QtItemIsEditable )
            dataItem.setData( QtDisplayRole, headerText )
            table.setItem( i, 1, dataItem )

            ## data preview
            dataItem = QTableWidgetItem()
            dataItem.setFlags( dataItem.flags() ^ QtItemIsEditable )
            dataItem.setData( QtDisplayRole, dataExample )
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
        showValue = tableItem.checkState() != QtUnchecked
        self.showColumn.emit( row, showValue )

    def getHeaderText(self, col):
        return self.oldHeaders.get( col, None )

    def isColumnVisible(self, col):
        return self.oldColumns.get( col, None )

#     def settingsAccepted(self):
#         ##restore old settings
#         pass

    def settingsRejected(self):
        ##restore old settings
        self.parentTable.setHeadersText( self.oldHeaders )
        self.parentTable.setColumnsVisibility( self.oldColumns )


## =========================================================


# pylint: disable=C0301
TableFiltersDialogUiClass, TableFiltersDialogBaseClass = uiloader.load_ui_from_module_path( "widget/tablefiltersdialog" )


class TableFiltersDialog(TableFiltersDialogBaseClass):           # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = TableFiltersDialogUiClass()
        self.ui.setupUi(self)

        self.parentTable: 'DataFrameTable'  = None
        self.oldState = None

        self.rejected.connect( self.settingsRejected )

    def connectTable( self, parentTable: 'DataFrameTable' ):
        self.parentTable = parentTable

        model = self.parentTable.model()
        self.oldState = model.filterState()                                     # type: ignore

        self.updateColumnsCombo()

        self.ui.conditionCB.setCurrentIndex( model.condition )                  # type: ignore

        filterValue = model.filterRegExp().pattern()                            # type: ignore
        self.ui.valueLE.setText( filterValue )

        self.ui.columnCB.currentIndexChanged.connect( self.columnChanged )
        self.ui.conditionCB.currentIndexChanged.connect( self.conditionChanged )
        self.ui.valueLE.textChanged.connect( self.valueChanged )

        self.parentTable.columnsConfigurationChanged.connect( self.updateColumnsCombo )

        self.adjustSize()

    def updateColumnsCombo(self):
        tableModel = self.parentTable.model()
        keyColumn = tableModel.filterKeyColumn()
        newIndex = 0
        self.ui.columnCB.clear()
        self.ui.columnCB.addItem( "No filtering", -1 )
        colsNum = tableModel.columnCount()
        for col in range(colsNum):
            text = tableModel.headerData(col, QtCore.Qt.Horizontal)
            if col == keyColumn:
                newIndex = self.ui.columnCB.count()
            if self.parentTable.isColumnHidden(col) is False:
                self.ui.columnCB.addItem( str(col) + " " + text, col )
        self.ui.columnCB.setCurrentIndex( newIndex )

    def columnChanged(self, _):
        self.updateFilter()

    def conditionChanged(self, _):
        self.updateFilter()

    def valueChanged(self, _):
        self.updateFilter()

    def updateFilter(self):
        model = self.parentTable.model()

        columnCBIndex = self.ui.columnCB.currentIndex()
        columnIndex = self.ui.columnCB.itemData( columnCBIndex )
        if columnIndex is None:
            return
        if columnIndex < 0:
            model.clearFilter()
            return

        model.setFilterKeyColumn( columnIndex )

        conditionIndex = self.ui.conditionCB.currentIndex()
        model.setFilterCondition( conditionIndex )

        filterText = self.ui.valueLE.text()
        model.setFilterFixedString( filterText )

    def settingsAccepted(self):
        pass

    def settingsRejected(self):
        self.parentTable.model().setFilterState( self.oldState )


## =========================================================


class TableRowColorDelegate():

    STOCK_FAV_BGCOLOR    = QColor( "beige" )
    STOCK_GRAY_BGCOLOR   = QColor( "#f0f0f0" )
    STOCK_WALLET_BGCOLOR = QColor( "palegreen" )

    def __init__(self):
        self.parent: 'DataFrameTableModel' = None

    def foreground(self, _: QModelIndex ):
        ## reimplement if needed
        return None

    def background(self, _: QModelIndex ):
        ## reimplement if needed
        return None

    def setParent(self, newParent):
        self.parent = newParent


class DataFrameTableModel( QAbstractTableModel ):

    def __init__(self, data: DataFrame):
        super().__init__()
        self._rawData: DataFrame                   = data
        self.customHeader: Dict[ int, str ]        = {}
        self.colorDelegate: TableRowColorDelegate  = None

    def setColorDelegate(self, decorator: TableRowColorDelegate):
        self.beginResetModel()
        self.colorDelegate = decorator
        decorator.setParent( self )
        self.endResetModel()

    def setContent(self, data: DataFrame):
        self.beginResetModel()
        self._rawData = data
        self.endResetModel()

    def setHeaders(self, headersDict, orientation=QtCore.Qt.Horizontal):
        self.customHeader = copy.deepcopy( headersDict )
        colsNum = self.columnCount()
        self.headerDataChanged.emit( orientation, 0, colsNum - 1 )

    # pylint: disable=W0613
    def rowCount(self, parent=None):
        if self._rawData is None:
            return 0
        return self._rawData.shape[0]

    # pylint: disable=W0613
    def columnCount(self, parnet=None):
        if self._rawData is None:
            return 0
        return self._rawData.shape[1]

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtDisplayRole:
            headerValue = self.customHeader.get( section, None )
            if headerValue is not None:
                return headerValue
            colName = self._rawData.columns[section]
            if isinstance(colName, tuple):
                return colName[0]
            return colName
        return super().headerData( section, orientation, role )

    def setHeaderData(self, section, orientation, value, _=QtDisplayRole):
        self.customHeader[ section ] = value
        self.headerDataChanged.emit( orientation, section, section )
        return True

    def data(self, index: QModelIndex, role=QtDisplayRole):
        if not index.isValid():
            return None

        if role == QtDisplayRole:
            rawData = self._rawData.iloc[index.row(), index.column()]
            strData = str(rawData)
            return strData
        if role == QtUserRole:
            rawData = self._rawData.iloc[index.row(), index.column()]
            return rawData
        if role == QtTextAlignmentRole:
            return QtAlignHCenter | QtAlignVCenter

        if self.colorDelegate is not None:
            if role == QtForegroundRole:
                return self.colorDelegate.foreground( index )
            if role == QtBackgroundRole:
                return self.colorDelegate.background( index )

        return None


## ===========================================================


def convert_to_qurl( strData ):
    parsed = urlparse( strData )
    if parsed.scheme in ("http", "https"):
        return QUrl( strData )
    return None


def contains_string( data ):
    if data == '-':
        return True
    if re.search( '[a-zA-Z:]', str(data) ):
        return True
    return False


class DFProxyModel( QtCore.QSortFilterProxyModel ):

    def __init__(self, parentObject=None):
        super().__init__(parentObject)

        ##  0 - greater than
        ##  1 - equal
        ##  2 - less than
        ##  3 - contains
        self.condition = 0

    def setFilterCondition(self, condition):
        self.condition = condition

    def lessThan(self, left: QModelIndex, right: QModelIndex):
        leftData  = self.sourceModel().data(left, QtUserRole)
        rightData = self.sourceModel().data(right, QtUserRole)
#         print("xxxxxxxx:", type(leftData), type(rightData) )
        return self.valueLessThan( leftData, rightData )

    def valueLessThan(self, leftData, rightData):
#         leftData, rightData = self.convertType( leftData, rightData )

        ## put no-data rows on bottom
        if is_invalid_number( leftData ):
            if self.sortOrder() == QtCore.Qt.AscendingOrder:
                return False
            return True
        if is_invalid_number( rightData ):
            if self.sortOrder() == QtCore.Qt.AscendingOrder:
                return True
            return False

        try:
            return leftData < rightData
        except TypeError:
            _LOGGER.warning( "unable to sort types: %s %s data: >%s< >%s<", type(leftData), type(rightData), leftData, rightData )
            return str(leftData) < str(rightData)

    def clearFilter(self):
        self.condition = 0
        self.setFilterFixedString( "" )

    def filterState(self):
        filterValue = self.filterRegExp().pattern()
        return [ self.filterKeyColumn(), self.condition, filterValue ]

    def setFilterState(self, state):
        self.setFilterKeyColumn( state[0] )
        self.condition = state[1]
        self.setFilterRegExp( state[2] )

    def filterAcceptsRow( self, sourceRow, sourceParent ):
        filterValue = self.filterRegExp().pattern()
        if not filterValue:
            ## empty filter -- accept all
            return True
        filterColumn = self.filterKeyColumn()
        valueIndex = self.sourceModel().index( sourceRow, filterColumn, sourceParent )
        rawValue = self.sourceModel().data( valueIndex, QtUserRole )
        value = str(rawValue)

        if self.condition == 0:
            ## greater than
            return self.valueLessThan( filterValue, value )
        if self.condition == 1:
            ## equal
            if self.valueLessThan( value, filterValue ):
                return False
            if self.valueLessThan( filterValue, value ):
                return False
            return True
        if self.condition == 2:
            ## less than
            return self.valueLessThan( value, filterValue )
        if self.condition == 3:
            ## contains
            strVal = str(value)
            return filterValue in strVal

        return False
#         return super().filterAcceptsRow( sourceRow, sourceParent )

    def convertType(self, leftData, rightData):
        if contains_string(leftData) or contains_string(rightData):
            return ( str(leftData), str(rightData) )

        #print("unable to detect type:", ascii(leftData), ascii(rightData) )
        return (leftData, rightData)


## ===========================================================


class DataFrameTable( QTableView ):

    columnsConfigurationChanged = pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("dataframetable")

        self._rawData = None
        self.columnsVisible: Dict[ int, bool ] = {}

        self.setSortingEnabled( True )
        self.setShowGrid( False )
        self.setAlternatingRowColors( True )

        header = self.horizontalHeader()
        header.setDefaultAlignment( QtCore.Qt.AlignCenter )
        header.setHighlightSections( False )
        header.setStretchLastSection( True )

        self.verticalHeader().hide()

        proxyModel = DFProxyModel(self)
        self.setModel( proxyModel )
        pandaModel = DataFrameTableModel( None )
        self.setSourceModel( pandaModel )

        self.setData( DataFrame() )

        self.doubleClicked.connect( self.linkClicked )

        self.installEventFilter( self )

    def setSourceModel(self, model):
        self.pandaModel = model
        proxyModel = self.model()
        proxyModel.setSourceModel( self.pandaModel )

    def addProxyModel(self, nextProxyModel):
        sinkModel   = self.model()
        sourceModel = sinkModel.sourceModel()
        nextProxyModel.setSourceModel( sourceModel )
        sinkModel.setSourceModel( nextProxyModel )

    @property
    def headersText(self):
        return self.pandaModel.customHeader

    def loadSettings(self, settings):
        wkey = guistate.get_widget_key(self, "tablesettings")
        settings.beginGroup( wkey )
        visDict = settings.value("columnsVisible", None, type=dict)
        if visDict is None:
            visDict = {}
        headersDict = settings.value("customHeaders", None, type=dict)
        settings.endGroup()
        self.setColumnsVisibility( visDict )
        if headersDict is not None:
            self.pandaModel.setHeaders( headersDict )

    def saveSettings(self, settings):
        wkey = guistate.get_widget_key(self, "tablesettings")
        settings.beginGroup( wkey )
        settings.setValue("columnsVisible", self.columnsVisible )
        settings.setValue("customHeaders", self.pandaModel.customHeader )
        settings.endGroup()

    def showColumnsConfiguration(self):
        if self._rawData is None:
            return
        dialog = TableSettingsDialog( self )
        dialog.connectTable( self )
        dialog.setData( self._rawData )
        dialog.show()

    def showFilterConfiguration(self):
        if self._rawData is None:
            return
        dialog = TableFiltersDialog( self )
        dialog.connectTable( self )
        dialog.show()

    def contextMenuEvent( self, _ ):
        contextMenu         = QMenu(self)
        filterDataAction    = contextMenu.addAction("Filter data")
        configColumnsAction = contextMenu.addAction("Configure columns")

        filterDataAction.triggered.connect( self.showFilterConfiguration )
        configColumnsAction.triggered.connect( self.showColumnsConfiguration )

        if self._rawData is None:
            configColumnsAction.setEnabled( False )

        globalPos = QCursor.pos()
        contextMenu.exec_( globalPos )

    ## ===============================================

    def clear(self):
        self.setData( None )

    def getSelectedIndexes(self):
        selection = self.selectionModel()
        return selection.selectedIndexes()

    ## column index is independent from column visibility
    ## it points to index in data source
    def getSelectedData(self, columnIndex):
        selectedIndexes = self.getSelectedIndexes()
        dataModel = self.model()
        ret = set()
        for dataRow in selectedIndexes:
            row = dataRow.row()
            parent = dataRow.parent()
            dataIndex = dataModel.index( row, columnIndex, parent )
            data = dataIndex.data()
            ret.add( data )
        return ret

    def setColorDelegate(self, decorator: TableRowColorDelegate):
        self.pandaModel.setColorDelegate( decorator )

    def setData(self, rawData: DataFrame ):
        self._rawData = rawData
        self.pandaModel.setContent( rawData )

    def setHeaderText(self, col, text):
        self.pandaModel.setHeaderData( col, QtCore.Qt.Horizontal, text )
        self.columnsConfigurationChanged.emit()

    def setColumnVisible(self, col, visible):
        self.columnsVisible[ col ] = visible
        self.setColumnHidden( col, not visible )
        self.columnsConfigurationChanged.emit()

    def setHeadersText(self, settingsDict ):
        self.pandaModel.setHeaders( settingsDict )
        self.columnsConfigurationChanged.emit()

    def setColumnsVisibility( self, settingsDict ):
        self.columnsVisible = settingsDict
        colsCount = self.pandaModel.columnCount()
        for col in range(0, colsCount):
            self.showColumn( col )
        for col, show in self.columnsVisible.items():
            self.setColumnHidden( col, not show )
        self.columnsConfigurationChanged.emit()

    def linkClicked(self, item: QModelIndex):
        itemData = item.data()
        url = convert_to_qurl( itemData )
        if url is not None:
            _LOGGER.info( "opening url: %s", url )
            QDesktopServices.openUrl( url )

    def settingsAccepted(self):
        ## do nothing -- reimplement if needed
        ## DO NOT REMOVE, reimplemented in inheriting classes
        pass

    def settingsRejected(self):
        ## do nothing -- reimplement if needed
        ## DO NOT REMOVE, reimplemented in inheriting classes
        pass

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if event.matches(QtGui.QKeySequence.Copy):
                self.copySelection()
                return True
        return super().eventFilter(source, event)

    def copySelection(self):
        selection = self.selectedIndexes()
        if not selection:
            return
        rows = sorted(index.row() for index in selection)
        columns = sorted(index.column() for index in selection)
        rowcount = rows[-1] - rows[0] + 1
        colcount = columns[-1] - columns[0] + 1
        table = [[''] * colcount for _ in range(rowcount)]
        for index in selection:
            row = index.row() - rows[0]
            column = index.column() - columns[0]
            table[row][column] = index.data()
        stream = io.StringIO()
        csv.writer(stream).writerows(table)
        QtWidgets.qApp.clipboard().setText(stream.getvalue())
