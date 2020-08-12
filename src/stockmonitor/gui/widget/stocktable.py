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
from PyQt5.QtGui import QDesktopServices

from .. import uiloader
from .. import guistate


_LOGGER = logging.getLogger(__name__)


UiTargetClass, QtBaseClass = uiloader.load_ui_from_module_path( "widget/tablesettingsdialog" )


class TableSettingsDialog(QtBaseClass):           # type: ignore

    setHeader  = pyqtSignal( int, str )
    showColumn = pyqtSignal( int, bool )

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
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

        self.ui.resizeColumnsPB.clicked.connect( parentTable.resizeColumnsToContents )

    def setData(self, rawData: DataFrame ):
        table = self.ui.columnsTable
        headerValues = rawData.columns.values
        rowsNum = rawData.shape[0]
        colsNum = rawData.shape[1]

        table.setRowCount( colsNum )

        for i in range(0, colsNum):
            headerText  = headerValues[i][0]
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

    def settingsAccepted(self):
        ##restore old settings
        self.parentTable.setHeadersText( self.oldHeaders )
        self.parentTable.setColumnsVisibility( self.oldColumns )

    def settingsRejected(self):
        ##restore old settings
        self.parentTable.setHeadersText( self.oldHeaders )
        self.parentTable.setColumnsVisibility( self.oldColumns )


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
        self.customHeader = headersDict
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
            return colName[0]
        return None

    def setHeaderData(self, section, orientation, value, _=Qt.DisplayRole):
        self.customHeader[ section ] = value
        self.headerDataChanged.emit( orientation, section, section )
        return True

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return str(self._rawData.iloc[index.row(), index.column()])
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

    def setColumnVisible(self, col, visible):
        self.columnsVisible[ col ] = visible
        self.setColumnHidden( col, not visible )

    def setHeadersText(self, settingsDict ):
        self.pandaModel.setHeaders( settingsDict )

    def setColumnsVisibility( self, settingsDict ):
        self.columnsVisible = settingsDict
        colsCount = self.pandaModel.columnCount()
        for col in range(0, colsCount):
            self.showColumn( col )
        for col, show in self.columnsVisible.items():
            self.setColumnHidden( col, not show )

    def settingsAccepted(self):
        ## do nothing -- reimplement if needed
        pass


## ====================================================================


class StockFullTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.dataObject = None

    def connectData(self, dataObject):
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

        if self._rawData is None:
            configColumnsAction.setEnabled( False )

        stockInfoAction = contextMenu.addAction("Stock info")

        globalPos = QCursor.pos()
        action = contextMenu.exec_( globalPos )

        if action == refreshAction:
            self.dataObject.refreshStockData()
        elif action == configColumnsAction:
            self.showColumnsConfiguration()
        elif action in favsActions:
            favGroup = action.data()
            self._addToFav( favGroup )
        elif action == stockInfoAction:
            self._openInfo()

    def _addToFav(self, favGrp):
        favList = self._getSelectedCodes()
        self.dataObject.addFav( favGrp, favList )

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
            code = dataAccess.getShortField( dataRow )
            favCodes.add( code )
        favList = list(favCodes)
        return favList

    def settingsAccepted(self):
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
        refreshAction       = contextMenu.addAction("Refresh data")
        configColumnsAction = contextMenu.addAction("Configure columns")
        remFavAction        = contextMenu.addAction("Remove fav")
        stockInfoAction     = contextMenu.addAction("Stock info")

        globalPos = QCursor.pos()
        action = contextMenu.exec_( globalPos )

        if action == refreshAction:
            self.dataObject.refreshStockData()
        elif action == configColumnsAction:
            self.showColumnsConfiguration()
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
