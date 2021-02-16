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
from datetime import time, timedelta, datetime

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QModelIndex
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtWidgets import QTableView

from stockmonitor.gui import guistate
from stockmonitor.gui.dataobject import DataObject
from stockmonitor.gui.datatypes import MarkersContainer, MarkerEntry
from stockmonitor.gui.widget.markerdialog import MarkerDialog

from .. import uiloader


_LOGGER = logging.getLogger(__name__)


class MarkersTableModel( QAbstractTableModel ):

    def __init__(self, data: MarkersContainer):
        super().__init__()
        self._rawData: MarkersContainer = data

    # pylint: disable=R0201
    def getItem(self, itemIndex: QModelIndex):
        if itemIndex.isValid():
            return itemIndex.internalPointer()
        return None

    def setContent(self, data: MarkersContainer):
        self.beginResetModel()
        self._rawData = data
        self.endResetModel()

    # pylint: disable=W0613
    def rowCount(self, parent=None):
        if self._rawData is None:
            return 0
        return self._rawData.size()

    # pylint: disable=W0613
    def columnCount(self, parnet=None):
        if self._rawData is None:
            return 0
        attrsList = self.attributeLabels()
        return len( attrsList )

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            attrsList = self.attributeLabels()
            return attrsList[ section ]
        return super().headerData( section, orientation, role )

    ## for invalid parent return elements form root list
    def index(self, row, column, parent: QModelIndex):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        entry = self._rawData.get( row )
        return self.createIndex(row, column, entry)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            entry = self._rawData.get( index.row() )
            rawData = self.attribute( entry, index.column() )
            if rawData is None:
                return "-"
            if isinstance(rawData, time):
                return rawData.strftime("%H:%M")
            if isinstance(rawData, timedelta):
                return print_timedelta( rawData )
            if isinstance(rawData, datetime):
                return rawData.strftime("%Y-%m-%d %H:%M")
            strData = str(rawData)
            return strData

        if role == Qt.UserRole:
            entry = self._rawData.get( index.row() )
            rawData = self.attribute( entry, index.column() )
            return rawData

        if role == Qt.EditRole:
            entry = self._rawData.get( index.row() )
            rawData = self.attribute( entry, index.column() )
            return rawData

        if role == Qt.TextAlignmentRole:
            if index.column() == 5:
                return Qt.AlignLeft | Qt.AlignVCenter
            return Qt.AlignHCenter | Qt.AlignVCenter

        return None

    def getIndex(self, item, parentIndex: QModelIndex=None, column: int = 0):
        if parentIndex is None:
            parentIndex = QModelIndex()
        if parentIndex.isValid():
            # dataTask = parentIndex.data( Qt.UserRole )
            dataTask = parentIndex.internalPointer()
            if dataTask == item:
                return parentIndex
        elems = self.rowCount( parentIndex )
        for i in range(elems):
            index = self.index( i, column, parentIndex )
            if index.isValid() is False:
                continue
            # dataTask = parentIndex.data( Qt.UserRole )
            dataTask = index.internalPointer()
            if dataTask == item:
                return index
        return None

    def attribute(self, entry: MarkerEntry, index):
        if index == 0:
            return entry.ticker
        elif index == 1:
            return entry.operationName()
        elif index == 2:
            return entry.value
        elif index == 3:
            return entry.amount
        elif index == 4:
            return entry.color
        elif index == 5:
            return entry.notes
        return None

    @staticmethod
    def attributeLabels():
        return ( "Ticker", "Typ operacji", "Kurs operacji", "Liczba", "Kolor", "Uwagi" )


## ===========================================================


class MarkersTable( QTableView ):

    selectedItem    = pyqtSignal( MarkerEntry )
    itemUnselected  = pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("markerstable")

        self.dataObject = None

        self.setSortingEnabled( True )
        self.setShowGrid( False )
        self.setAlternatingRowColors( True )
#         self.setEditTriggers( QAbstractItemView.DoubleClicked )

        header = self.horizontalHeader()
        header.setDefaultAlignment( Qt.AlignCenter )
        header.setHighlightSections( False )
        header.setStretchLastSection( True )

        self.verticalHeader().hide()

        self.dataModel = MarkersTableModel( None )
        self.proxyModel = QtCore.QSortFilterProxyModel(self)
        self.proxyModel.setSourceModel( self.dataModel )
        self.setModel( self.proxyModel )

    def loadSettings(self, settings):
        wkey = guistate.get_widget_key(self, "tablesettings")
        settings.beginGroup( wkey )
        visDict = settings.value("columnsVisible", None, type=dict)
        if visDict is None:
            visDict = dict()

    def saveSettings(self, settings):
        wkey = guistate.get_widget_key(self, "tablesettings")
        settings.beginGroup( wkey )
        settings.setValue("columnsVisible", self.columnsVisible )
        settings.endGroup()

    ## ===============================================

    def connectData(self, dataObject: DataObject ):
        self.dataObject = dataObject
#         self.dataObject.feedChanged.connect( self.refreshData )
        self.refreshData()

    def refreshData(self):
        markers: MarkersContainer = self.dataObject.markers
        self.dataModel.setContent( markers )
        self.clearSelection()
#         _LOGGER.debug( "entries: %s\n%s", type(history), history.printData() )

    def refreshEntry(self, entry: MarkerEntry=None):
        if entry is None:
            ## unable to refresh entry row -- refresh whole model
            self.refreshData()
            return
        taskIndex = self.getIndex( entry )
        if taskIndex is None:
            ## unable to refresh entry row -- refresh whole model
            self.refreshData()
            return
        lastColIndex = taskIndex.sibling( taskIndex.row(), 4 )
        if lastColIndex is None:
            ## unable to refresh entry row -- refresh whole model
            self.refreshData()
            return
        self.proxyModel.dataChanged.emit( taskIndex, lastColIndex )

    def getIndex(self, entry: MarkerEntry, column: int = 0):
        modelIndex = self.dataModel.getIndex( entry, column=column )
        if modelIndex is None:
            return None
        proxyIndex = self.proxyModel.mapFromSource( modelIndex )
        return proxyIndex

    def getItem(self, itemIndex: QModelIndex ) -> MarkerEntry:
        sourceIndex = self.proxyModel.mapToSource( itemIndex )
        return self.dataModel.getItem( sourceIndex )

    def contextMenuEvent( self, event ):
        evPos            = event.pos()
        entry: MarkerEntry = None
        mIndex = self.indexAt( evPos )
        if mIndex is not None:
            entry = self.getItem( mIndex )

        contextMenu      = QtWidgets.QMenu( self )
        addAction        = contextMenu.addAction("Add Marker")
        editAction       = contextMenu.addAction("Edit Marker")
        removeAction     = contextMenu.addAction("Remove Marker")

        if entry is None:
            editAction.setEnabled( False )
            removeAction.setEnabled( False )

        globalPos = QtGui.QCursor.pos()
        action = contextMenu.exec_( globalPos )

        if action == addAction:
            self._addEntry()
        elif action == editAction:
            self._editEntry( entry )
        elif action == removeAction:
            self._removeEntry( entry )

    def currentChanged(self, current, previous):
        super().currentChanged( current, previous )
        item = self.getItem( current )
        if item is not None:
            self.selectedItem.emit( item )
        else:
            self.itemUnselected.emit()

    def mouseDoubleClickEvent( self, event ):
        evPos               = event.pos()
        entry: MarkerEntry = None
        mIndex = self.indexAt( evPos )
        if mIndex is not None:
            entry = self.getItem( mIndex )

        if entry is None:
            self._addEntry()
        else:
            self._editEntry( entry )

        return super().mouseDoubleClickEvent(event)

    def _addEntry(self):
        parentWidget = self.parent()
        entryDialog = MarkerDialog( None, parentWidget )
        entryDialog.setModal( True )
        dialogCode = entryDialog.exec_()
        if dialogCode == QtWidgets.QDialog.Rejected:
            return
        _LOGGER.debug( "adding entry: %s", entryDialog.entry.printData() )
        self.dataObject.addMarkerEntry( entryDialog.entry )

    def _editEntry(self, entry):
#         self.dataObject.editMarkerEntry( entry )
        parentWidget = self.parent()
        entryDialog = MarkerDialog( entry, parentWidget )
        entryDialog.setModal( True )
        dialogCode = entryDialog.exec_()
        if dialogCode == QtWidgets.QDialog.Rejected:
            return
        _LOGGER.debug( "replacing entry: %s", entryDialog.entry.printData() )
        self.dataObject.replaceMarkerEntry( entry, entryDialog.entry )

    def _removeEntry(self, entry):
        self.dataObject.removeMarkerEntry( entry )


def print_timedelta( value: timedelta ):
    s = ""
    secs = value.seconds
    days = value.days
    if secs != 0 or days == 0:
        mm, _ = divmod(secs, 60)
        hh, mm = divmod(mm, 60)
        s = "%d:%02d" % (hh, mm)
#         s = "%d:%02d:%02d" % (hh, mm, ss)
    if days:
        def plural(n):
            return n, abs(n) != 1 and "s" or ""
        if s != "":
            s = ("%d day%s, " % plural(days)) + s
        else:
            s = ("%d day%s" % plural(days)) + s
#     micros = value.microseconds
#     if micros:
#         s = s + ".%06d" % micros
    return s


# class StockFavsColorDelegate( TableRowColorDelegate ):
#
#     def __init__(self, dataObject: DataObject):
#         super().__init__()
#         self.dataObject = dataObject
#
# #     def foreground(self, index: QModelIndex ):
# #         ## reimplement if needed
# #         return None
#
#     def background(self, index: QModelIndex ):
#         sourceParent = index.parent()
#         dataRow = index.row()
#         dataIndex = self.parent.index( dataRow, 3, sourceParent )       ## get name
#         ticker = dataIndex.data()
#         return wallet_background_color( self.dataObject, ticker )


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class MarkersWidget( QtBaseClass ):           # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.dataObject = None

    def connectData(self, dataObject):
        self.dataObject = dataObject
        self.dataObject.markersChanged.connect( self.updateView )
        self.ui.markersTable.connectData( dataObject )
        self.updateView()

    def updateView(self):
        self.ui.markersTable.refreshData()

#         if self.dataObject is None:
#             _LOGGER.warning("unable to update view")
#             self.ui.data_tabs.clear()
#             return
#         favsObj = self.dataObject.favs
#         favKeys = favsObj.getFavGroups()
#
#         _LOGGER.info("updating view: %s %s", favKeys, self.tabsList() )
#
#         tabsNum = self.ui.data_tabs.count()
#
#         for i in reversed( range(tabsNum) ):
#             tabName = self.tabText( i )
#             if tabName not in favKeys:
#                 _LOGGER.info("removing tab: %s %s", i, tabName)
#                 self.removeTab( i )
#
#         i = -1
#         for favName in favKeys:
#             i += 1
#             tabIndex = self.findTabIndex( favName )
#             if tabIndex < 0:
#                 _LOGGER.debug("adding tab: %s", favName)
#                 self.addTab( favName )
#
#         self.updateOrder()

#     def updateTab(self, tabName):
#         _LOGGER.info("updating tab: %s", tabName)
#         tabIndex = self.findTabIndex( tabName )
#         pageWidget: SinglePageWidget = self.ui.data_tabs.widget( tabIndex )
#         if pageWidget is not None:
#             pageWidget.updateView()

#     def updateOrder(self):
#         if self.dataObject is None:
#             _LOGGER.warning("unable to reorder view")
#             return
#         favsObj = self.dataObject.favs
#         _LOGGER.info("updating order")
#         favKeys = favsObj.getFavGroups()
#         tabBar = self.ui.data_tabs.tabBar()
#         tabBar.tabMoved.disconnect( self.tabMoved )
#         i = -1
#         for key in favKeys:
#             i += 1
#             tabIndex = self.findTabIndex( key )
#             if tabIndex < 0:
#                 continue
#             if tabIndex != i:
#                 _LOGGER.warning("moving tab %s from %s to %s", key, tabIndex, i)
#                 tabBar.moveTab( tabIndex, i )
#         tabBar.tabMoved.connect( self.tabMoved )

#     def addTab(self, favGroup):
#         pageWidget = SinglePageWidget(self)
#         pageWidget.setData( self.dataObject, favGroup )
#         self.ui.data_tabs.addTab( pageWidget, favGroup )
#
#     def removeTab(self, tabIndex):
#         widget = self.ui.data_tabs.widget( tabIndex )
#         widget.setParent( None )
#         del widget

#     def loadSettings(self, settings):
#         tabsSize = self.ui.data_tabs.count()
#         for tabIndex in range(0, tabsSize):
#             pageWidget = self.ui.data_tabs.widget( tabIndex )
#             pageWidget.loadSettings( settings )
#
#     def saveSettings(self, settings):
#         tabsSize = self.ui.data_tabs.count()
#         for tabIndex in range(0, tabsSize):
#             pageWidget = self.ui.data_tabs.widget( tabIndex )
#             pageWidget.saveSettings( settings )
#
#     def findTabIndex(self, tabName):
#         for ind in range(0, self.ui.data_tabs.count()):
#             tabText = self.tabText( ind )
#             if tabText == tabName:
#                 return ind
#         return -1
#
#     def tabsList(self):
#         ret = []
#         for ind in range(0, self.ui.data_tabs.count()):
#             tabText = self.tabText( ind )
#             ret.append( tabText )
#         return ret
#
#     def contextMenuEvent( self, event ):
#         evPos     = event.pos()
#         globalPos = self.mapToGlobal( evPos )
#         tabBar    = self.ui.data_tabs.tabBar()
#         tabPos    = tabBar.mapFromGlobal( globalPos )
#         tabIndex  = tabBar.tabAt( tabPos )
#
#         contextMenu   = QMenu(self)
#         newAction     = contextMenu.addAction("New")
#         renameAction  = contextMenu.addAction("Rename")
#         deleteAction  = contextMenu.addAction("Delete")
#
#         if tabIndex < 0:
#             renameAction.setEnabled( False )
#             deleteAction.setEnabled( False )
#
#         action = contextMenu.exec_( globalPos )
#
#         if action == newAction:
#             self._newTabRequest()
#         elif action == renameAction:
#             self._renameTabRequest( tabIndex )
#         elif action == deleteAction:
#             ticker = self.tabText( tabIndex )
#             self.removeFavGrp.emit( ticker )
#
#     def tabMoved(self):
#         favOrder = self.tabsList()
#         self.dataObject.reorderFavGroups( favOrder )
#
#     def _newTabRequest( self ):
#         newTitle = self._requestTabName( "Favs" )
#         if len(newTitle) < 1:
#             return
#         self.addFavGrp.emit( newTitle )
#
#     def _renameTabRequest( self, tabIndex ):
#         if tabIndex < 0:
#             return
#         oldTitle = self.tabText( tabIndex )
#         newTitle = self._requestTabName(oldTitle)
#         if not newTitle:
#             # empty
#             return
#         self.renameFavGrp.emit( oldTitle, newTitle )
#
#     def tabText(self, index):
#         name = self.ui.data_tabs.tabText( index )
#         name = name.replace("&", "")
#         return name
#
#     def _requestTabName( self, currName ):
#         newText, ok = QInputDialog.getText( self,
#                                             "Rename Fav Group",
#                                             "Fav Group name:",
#                                             QLineEdit.Normal,
#                                             currName )
#         if ok and newText:
#             # not empty
#             return newText
#         return ""
#
#     def _renameTab(self, fromName, toName):
#         tabIndex = self.findTabIndex( fromName )
#         if tabIndex < 0:
#             self.updateView()
#             return
#         tabWidget: SinglePageWidget = self.ui.data_tabs.widget( tabIndex )
#         if tabWidget is None:
#             self.updateView()
#             return
#         tabWidget.setData( self.dataObject, toName )
#         tabBar = self.ui.data_tabs.tabBar()
#         tabBar.setTabText( tabIndex, toName )
