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

from typing import Dict, List

from urllib.parse import urlparse
from pandas import DataFrame

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QModelIndex, QUrl
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtWidgets import QTableView, QTableWidgetItem
from PyQt5.QtWidgets import QMenu, QInputDialog
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QCursor
from PyQt5.QtGui import QDesktopServices

from .. import uiloader
from .. import guistate


_LOGGER = logging.getLogger(__name__)


# pylint: disable=C0301
TableSettingsDialogUiClass, TableSettingsDialogBaseClass = uiloader.load_ui_from_module_path( "widget/tablesettingsdialog" )


class TableSettingsDialog(TableSettingsDialogBaseClass):           # type: ignore

    setHeader  = pyqtSignal( int, str )
    showColumn = pyqtSignal( int, bool )

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = TableSettingsDialogUiClass()
        self.ui.setupUi(self)

        self.parentTable: 'StockTable'  = None

        self.oldHeaders = None
        self.oldColumns = None

        table = self.ui.columnsTable
        table.cellChanged.connect( self.tableCellChanged )
        self.rejected.connect( self.settingsRejected )

    def connectTable( self, parentTable: 'StockTable' ):
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
            checkedState = Qt.Checked
            colVisible = self.isColumnVisible( i )
            if colVisible is not None and colVisible is False:
                checkedState = Qt.Unchecked
            dataItem.setCheckState( checkedState )
            userText = self.getHeaderText( i )
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

        self.parentTable: 'StockTable'  = None
        self.oldState = None

        self.rejected.connect( self.settingsRejected )

    def connectTable( self, parentTable: 'StockTable' ):
        self.parentTable = parentTable

        model = self.parentTable.model()
        self.oldState = model.filterState()

        self.updateColumnsCombo()

        self.ui.conditionCB.setCurrentIndex( model.condition )

        filterValue = model.filterRegExp().pattern()
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
        self.ui.columnCB.addItem( "None", -1 )
        colsNum = tableModel.columnCount()
        for col in range(colsNum):
            text = tableModel.headerData(col, Qt.Horizontal)
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


class PandasModel( QAbstractTableModel ):

    def __init__(self, data: DataFrame):
        super().__init__()
        self._rawData: DataFrame = data
        self.customHeader: Dict[ int, str ] = dict()

    def setContent(self, data: DataFrame):
        self.beginResetModel()
        self._rawData = data
        self.endResetModel()

    def setHeaders(self, headersDict, orientation=Qt.Horizontal):
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
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            headerValue = self.customHeader.get( section, None )
            if headerValue is not None:
                return headerValue
            colName = self._rawData.columns[section]
            if isinstance(colName, tuple):
                return colName[0]
            return colName
        return None

    def setHeaderData(self, section, orientation, value, _=Qt.DisplayRole):
        self.customHeader[ section ] = value
        self.headerDataChanged.emit( orientation, section, section )
        return True

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            rawData = self._rawData.iloc[index.row(), index.column()]
            strData = str(rawData)
            return strData
        if role == Qt.TextAlignmentRole:
            return Qt.AlignHCenter | Qt.AlignVCenter
        return None


def convert_to_qurl( strData ):
    parsed = urlparse( strData )
    if parsed.scheme in ("http", "https"):
        return QUrl( strData )
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

    def __init__(self, parentObject=None):
        super().__init__(parentObject)

        ##  0 - greater than
        ##  1 - equal
        ##  2 - less than
        self.condition = 0

    def setFilterCondition(self, condition):
        self.condition = condition

    def lessThan(self, left: QModelIndex, right: QModelIndex):
        leftData  = self.sourceModel().data(left, QtCore.Qt.DisplayRole)
        rightData = self.sourceModel().data(right, QtCore.Qt.DisplayRole)
        return self.valueLessThan( leftData, rightData )

    def valueLessThan(self, leftData, rightData):
        leftData, rightData  = self.convertType( leftData, rightData )
        return leftData < rightData

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
        filterColumn = self.filterKeyColumn()
        filterValue = self.filterRegExp().pattern()
        valueIndex = self.sourceModel().index( sourceRow, filterColumn, sourceParent )
        value = self.sourceModel().data( valueIndex )

        if self.condition > 1:
            ## less than
            return self.valueLessThan( value, filterValue )
        elif self.condition < 1:
            ## greater than
            return self.valueLessThan( filterValue, value )

        ## equal
        if self.valueLessThan( value, filterValue ):
            return False
        if self.valueLessThan( filterValue, value ):
            return False
        return True

#         return super().filterAcceptsRow( sourceRow, sourceParent )

    def convertType(self, leftData, rightData):
        if contains_string(leftData) or contains_string(rightData):
            return ( str(leftData), str(rightData) )

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

    columnsConfigurationChanged = pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("stocktable")

        self._rawData = None
        self.columnsVisible: Dict[ int, bool ] = dict()

        self.setSortingEnabled( True )
        self.setShowGrid( False )
        self.setAlternatingRowColors( True )

        header = self.horizontalHeader()
        header.setDefaultAlignment( Qt.AlignCenter )
        header.setHighlightSections( False )
        header.setStretchLastSection( True )

        self.pandaModel = PandasModel( None )
        proxyModel = TaskSortFilterProxyModel(self)
        proxyModel.setSourceModel( self.pandaModel )
        self.setModel( proxyModel )

        self.setData( DataFrame() )

        self.doubleClicked.connect( self.linkClicked )

    @property
    def headersText(self):
        return self.pandaModel.customHeader

    def loadSettings(self, settings):
        settings.beginGroup( guistate.get_widget_key(self, "tablesettings") )
        visDict = settings.value("columnsVisible", None, type=dict)
        if visDict is None:
            visDict = dict()
        settings.endGroup()
        self.setColumnsVisibility( visDict )

    def saveSettings(self, settings):
        settings.beginGroup( guistate.get_widget_key(self, "tablesettings") )
        settings.setValue("columnsVisible", self.columnsVisible )
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
        configColumnsAction = contextMenu.addAction("Configure columns")

        if self._rawData is None:
            configColumnsAction.setEnabled( False )

        globalPos = QCursor.pos()
        action = contextMenu.exec_( globalPos )

        if action == configColumnsAction:
            self.showColumnsConfiguration()

    ## ===============================================

    def setData(self, rawData: DataFrame ):
        self._rawData = rawData
        self.pandaModel.setContent( rawData )

    def setHeaderText(self, col, text):
        self.pandaModel.setHeaderData( col, Qt.Horizontal, text )
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
            QDesktopServices.openUrl( url )

    def settingsAccepted(self):
        ## do nothing -- reimplement if needed
        ## DO NOT REMOVE, reimplemented in inheriting classes
        pass

    def settingsRejected(self):
        ## do nothing -- reimplement if needed
        ## DO NOT REMOVE, reimplemented in inheriting classes
        pass


## ====================================================================


class DataStockTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.dataObject = None

    def connectData(self, dataObject):
        self.dataObject = dataObject

    def contextMenuEvent( self, _ ):
        contextMenu         = QMenu(self)
        stockInfoAction = contextMenu.addAction("Stock info")
        favsActions = self._addFavActions( contextMenu )
        contextMenu.addSeparator()

        filterDataAction = contextMenu.addAction("Filter data")
        configColumnsAction = contextMenu.addAction("Configure columns")
        if self._rawData is None:
            configColumnsAction.setEnabled( False )

        globalPos = QCursor.pos()
        action = contextMenu.exec_( globalPos )

        if action == configColumnsAction:
            self.showColumnsConfiguration()
        elif action == filterDataAction:
            self.showFilterConfiguration()
        elif action in favsActions:
            favGroup = action.data()
            self._addToFav( favGroup )
        elif action == stockInfoAction:
            self._openInfo()

    def _addFavActions(self, contextMenu):
        favsActions = []
        if self.dataObject is not None:
            favSubMenu    = contextMenu.addMenu("Add to favs")
            favGroupsList = self.dataObject.favs.favGroupsList()
            for favGroup in favGroupsList:
                favAction = favSubMenu.addAction( favGroup )
                favAction.setData( favGroup )
                favsActions.append( favAction )
            newFavGroupAction = favSubMenu.addAction( "New group ..." )
            newFavGroupAction.setData( None )
            favsActions.append( newFavGroupAction )
        return favsActions

    def _addToFav(self, favGrp):
        if favGrp is None:
            newText, ok = QInputDialog.getText( self,
                                                "Rename Fav Group",
                                                "Fav Group name:",
                                                QLineEdit.Normal,
                                                "Favs" )
            if ok and newText:
                # not empty
                favGrp = newText
            else:
                return
        favList = self._getSelectedCodes()
        self.dataObject.addFav( favGrp, favList )

    def _openInfo(self):
        dataAccess = self.dataObject.currentStockData
        favList = self._getSelectedCodes()
        for code in favList:
            infoLink = dataAccess.getInfoLinkFromCode( code )
            QDesktopServices.openUrl( QtCore.QUrl(infoLink) )

    def _getSelectedCodes(self) -> List[str]:
        ## reimplement if needed
        return list()


## ====================================================================


class StockFullTable( DataStockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("stockfulltable")

    def connectData(self, dataObject):
        super().connectData( dataObject )
        self.dataObject = dataObject
        self.dataObject.stockDataChanged.connect( self.updateData )
        self.dataObject.stockHeadersChanged.connect( self.updateView )
        self.updateData()
        self.updateView()

    def updateData(self):
        dataAccess = self.dataObject.currentStockData
        dataframe = dataAccess.getWorksheet( False )
        self.setData( dataframe )

    def updateView(self):
        self.setHeadersText( self.dataObject.currentStockHeaders )

    def _getSelectedCodes(self):
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
        return favList

    def settingsAccepted(self):
        self.dataObject.setCurrentStockHeaders( self.pandaModel.customHeader )

    def settingsRejected(self):
        self.dataObject.setCurrentStockHeaders( self.pandaModel.customHeader )


## ====================================================================


class StockFavsTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("stockfavstable")
        self.dataObject = None
        self.favGroup = None

    def connectData(self, dataObject, favGroup):
        self.dataObject = dataObject
        self.favGroup = favGroup
        if self.dataObject is None:
            return
        self.dataObject.stockDataChanged.connect( self.updateData )
        self.dataObject.stockHeadersChanged.connect( self.updateView )
        self.updateData()
        self.updateView()

    def updateData(self):
        dataframe = self.dataObject.getFavStock( self.favGroup )
        self.setData( dataframe )

    def updateView(self):
        self.setHeadersText( self.dataObject.currentStockHeaders )

    def contextMenuEvent( self, _ ):
        contextMenu         = QMenu(self)
        stockInfoAction     = contextMenu.addAction("Stock info")
        remFavAction        = contextMenu.addAction("Remove fav")
        contextMenu.addSeparator()
        filterDataAction = contextMenu.addAction("Filter data")
        configColumnsAction = contextMenu.addAction("Configure columns")

        globalPos = QCursor.pos()
        action = contextMenu.exec_( globalPos )

        if action == configColumnsAction:
            self.showColumnsConfiguration()
        elif action == filterDataAction:
            self.showFilterConfiguration()
        elif action == remFavAction:
            favList = self._getSelectedCodes()
            self.dataObject.deleteFav( self.favGroup, favList )
        elif action == stockInfoAction:
            self._openInfo()

    def _openInfo(self):
        dataAccess = self.dataObject.currentStockData
        favList = self._getSelectedCodes()
        for code in favList:
            infoLink = dataAccess.getInfoLinkFromCode( code )
            QDesktopServices.openUrl( QtCore.QUrl(infoLink) )

    def _getSelectedCodes(self):
        dataAccess = self.dataObject.currentStockData
        selection = self.selectionModel()
        indexes = selection.selectedIndexes()
        favCodes = set()
        for ind in indexes:
            sourceIndex = self.model().mapToSource( ind )
            dataRow = sourceIndex.row()
            code = dataAccess.getShortFieldFromData( self._rawData, dataRow )
            favCodes.add( code )
        favList = list(favCodes)
        return favList

    def settingsAccepted(self):
        self.dataObject.setCurrentStockHeaders( self.pandaModel.customHeader )

    def settingsRejected(self):
        self.dataObject.setCurrentStockHeaders( self.pandaModel.customHeader )


## ====================================================================


class ToolStockTable( DataStockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("toolstocktable")

    def _getSelectedCodes(self):
        dataAccess = self.dataObject.currentStockData
        selection = self.selectionModel()
        indexes = selection.selectedIndexes()
        favCodes = set()
        for ind in indexes:
            sourceIndex = self.model().mapToSource( ind )
            dataRow = sourceIndex.row()
            stockName = self._rawData.iloc[dataRow, 0]
            code = dataAccess.getShortFieldByName( stockName )
            if code is not None:
                favCodes.add( code )
        favList = list(favCodes)
        return favList
