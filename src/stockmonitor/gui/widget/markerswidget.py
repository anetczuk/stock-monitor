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
from datetime import timedelta

from PyQt5 import QtWidgets
from PyQt5.QtCore import QModelIndex

## workaround for mypy type errors
from PyQt5.QtCore import Qt

from stockmonitor.datatypes.datatypes import MarkerEntry
from stockmonitor.gui.dataobject import DataObject
from stockmonitor.gui.widget.markerdialog import MarkerDialog
from stockmonitor.gui.widget.dataframetable import DataFrameTableModel,\
    TableRowColorDelegate
from stockmonitor.gui.widget.stocktable import StockTable, insert_new_action
from stockmonitor.gui.widget.stocktable import marker_background_color

from .. import uiloader


QtDisplayRole = Qt.DisplayRole                  # type: ignore
QtTextAlignmentRole = Qt.TextAlignmentRole      # type: ignore
QtAlignLeft = Qt.AlignLeft                      # type: ignore
QtAlignVCenter = Qt.AlignVCenter                # type: ignore


_LOGGER = logging.getLogger(__name__)


class MarkersTableModel( DataFrameTableModel ):

#     def __init__(self, data: DataFrame):
#         super().__init__( data )

    def data(self, index: QModelIndex, role=QtDisplayRole):
        if not index.isValid():
            return None

#         if role == QtDisplayRole:
#             retValue = super().data( index, role )
#             if retValue is None or retValue == "None":
#                 return "-"
#             return retValue

        if role == QtTextAlignmentRole:
            if index.column() == 10:
                ## notes
                return QtAlignLeft | QtAlignVCenter
#             return Qt.AlignHCenter | QtAlignVCenter

        return super().data( index, role )


## ===========================================================


class MarkersColorDelegate( TableRowColorDelegate ):

    def __init__(self, dataObject: DataObject):
        super().__init__()
        self.dataObject = dataObject

#     def foreground(self, index: QModelIndex ):
#         ## reimplement if needed
#         return None

    def background(self, index: QModelIndex ):
        sourceParent = index.parent()
        dataRow = index.row()
        dataIndex = self.parent.index( dataRow, 1, sourceParent )       ## get ticker
        ticker = dataIndex.data()
        return marker_background_color( self.dataObject, ticker )


## ===========================================================


class MarkersTable( StockTable ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("markerstable")

        markersModel = MarkersTableModel( None )
        self.setSourceModel( markersModel )

    def connectData(self, dataObject):
        super().connectData( dataObject )

        colorDecorator = MarkersColorDelegate( dataObject )
        self.setColorDelegate( colorDecorator )

        self.refreshData()

    def refreshData(self):
        _LOGGER.info( "updating view" )
        markersData = self.dataObject.getMarkersData()
        self.setData( markersData )
        self.clearSelection()
#         _LOGGER.debug( "entries: %s\n%s", type(history), history.printData() )

    def getItem(self, itemIndex: QModelIndex ) -> MarkerEntry:
        if self.dataObject is None:
            return None
        sourceIndex = self.model().mapToSource( itemIndex )         # type: ignore
#         return self.dataModel.getItem( sourceIndex )
        markerIndex = sourceIndex.row()
        if markerIndex < 0:
            return None
        return self.dataObject.markers.get( markerIndex )

    ## override
    def createContextMenu(self, itemIndex):
        contextMenu = super().createContextMenu( itemIndex )

        entry: MarkerEntry = None
        if itemIndex is not None:
            entry = self.getItem( itemIndex )

        addAction = insert_new_action( contextMenu, "Add Marker", 0 )
#         addAction = contextMenu.addAction("Add Marker")
        addAction.triggered.connect( self._addEntry )

        editAction = insert_new_action( contextMenu, "Edit Marker", 1 )
#         editAction = contextMenu.addAction("Edit Marker")
        editAction.setData( entry )
        editAction.triggered.connect( self._editEntryAction )

        removeAction = insert_new_action( contextMenu, "Remove Marker", 2 )
#         removeAction = contextMenu.addAction("Remove Marker")
        removeAction.setData( entry )
        removeAction.triggered.connect( self._removeEntryAction )

        ## add separator
        insert_new_action( contextMenu, None, 3 )

        if entry is None:
            editAction.setEnabled( False )
            removeAction.setEnabled( False )

        return contextMenu

    def mouseDoubleClickEvent( self, event ):
        evPos              = event.pos()
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

    def _editEntryAction(self):
        parentAction = self.sender()
        entry = parentAction.data()
        if entry is None:
            return
        self._editEntry( entry )

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

    def _removeEntryAction(self):
        parentAction = self.sender()
        entry = parentAction.data()
        if entry is None:
            return
        self._removeEntry( entry )

    def _removeEntry(self, entry):
        self.dataObject.removeMarkerEntry( entry )

    def _getSelectedTickers(self):
        selectedData = self.getSelectedData( 1 )                ## ticker
        return selectedData


def print_timedelta( value: timedelta ):
    s = ""
    secs = value.seconds
    days = value.days
    if secs != 0 or days == 0:
        mm, _ = divmod(secs, 60)
        hh, mm = divmod(mm, 60)
        s = f"{hh}:{mm:02}"
#         s = "%d:%02d" % (hh, mm)
#         s = "%d:%02d:%02d" % (hh, mm, ss)
    if days:
        def plural(n):
            return n, abs(n) != 1 and "s" or ""
        if s != "":
            s = ("%d day%s, " % plural(days)) + s               # pylint: disable=C0209
        else:
            s = ("%d day%s" % plural(days)) + s                 # pylint: disable=C0209
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
        self.ui.markersTable.connectData( dataObject )
        self.dataObject.stockDataChanged.connect( self.updateView )
        self.dataObject.markersChanged.connect( self.updateView )
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
