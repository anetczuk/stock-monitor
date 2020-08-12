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
# from datetime import datetime

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMenu, QInputDialog
from PyQt5.QtWidgets import QLineEdit

from .. import uiloader
from .stocktable import StockFavsTable


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


_LOGGER = logging.getLogger(__name__)


class SinglePageWidget( QWidget ):

    contentChanged = pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.content = ""
        self.changeCounter = 0

        vlayout = QVBoxLayout()
        vlayout.setContentsMargins( 0, 0, 0, 0 )
        self.setLayout( vlayout )
        self.stockData = StockFavsTable(self)

        vlayout.addWidget( self.stockData )

    def setData(self, dataObject, favGroup):
        self.setObjectName( favGroup )
        self.stockData.connectData( dataObject, favGroup )

    def loadSettings(self, settings):
        self.stockData.loadSettings( settings )

    def saveSettings(self, settings):
        self.stockData.saveSettings( settings )


class FavsWidget( QtBaseClass ):           # type: ignore

    addFavGrp    = pyqtSignal( str )
    renameFavGrp = pyqtSignal( str, str )
    removeFavGrp = pyqtSignal( str )

    favsChanged  = pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.dataObject = None

        tabBar = self.ui.data_tabs.tabBar()
        tabBar.tabMoved.connect( self.tabMoved )

        self.ui.data_tabs.clear()

    def connectData(self, dataObject):
        self.dataObject = dataObject
        self.dataObject.stockDataChanged.connect( self.updateView )
        self.dataObject.favsChanged.connect( self.updateView )
        self.dataObject.favsReordered.connect( self.updateOrder )
        self.updateView()

    def updateView(self):
        if self.dataObject is None:
            _LOGGER.warning("unable to update view")
            self.ui.data_tabs.clear()
            return
        _LOGGER.info("updating view")
        favsObj = self.dataObject.favs
        dataDict = favsObj.favs
        favKeys = dataDict.keys()

        tabsNum = self.ui.data_tabs.count()
        
        for i in reversed( range(tabsNum) ):
            tabName = self.ui.data_tabs.tabText( i )
            if tabName not in favKeys:
                self.removeTab( i )
        
        i = -1
        for favName in favKeys:
            i += 1
            tabIndex = self.findTabIndex( favName )
            if tabIndex < 0:
                self.addTab( favName )
                continue
            if tabIndex != i:
                _LOGGER.warning("unhandled case - tab moved: %s %s %s", favName, tabIndex, i)

    def updateOrder(self):
        if self.dataObject is None:
            _LOGGER.warning("unable to reorder view")
            return
        tabBar = self.ui.data_tabs.tabBar()
        tabBar.tabMoved.disconnect( self.tabMoved )
        favsObj = self.dataObject.favs
        dataDict = favsObj.favs
        favKeys = dataDict.keys()
        i = -1
        for key in favKeys:
            i += 1
            tabIndex = self.findTabIndex( key )
            if tabIndex < 0:
                continue
            tabBar.moveTab( tabIndex, i )
        tabBar.tabMoved.connect( self.tabMoved )

    def addTab(self, favGroup):
        pageWidget = SinglePageWidget(self)
        pageWidget.setData( self.dataObject, favGroup )
        self.ui.data_tabs.addTab( pageWidget, favGroup )

    def removeTab(self, tabIndex):
        widget = self.ui.data_tabs.widget( tabIndex )
        widget.setParent( None )
        del widget

    def loadSettings(self, settings):
        tabsSize = self.ui.data_tabs.count()
        for tabIndex in range(0, tabsSize):
            pageWidget = self.ui.data_tabs.widget( tabIndex )
            pageWidget.loadSettings( settings )

    def saveSettings(self, settings):
        tabsSize = self.ui.data_tabs.count()
        for tabIndex in range(0, tabsSize):
            pageWidget = self.ui.data_tabs.widget( tabIndex )
            pageWidget.saveSettings( settings )

    def findTabIndex(self, tabName):
        for ind in range(0, self.ui.data_tabs.count()):
            tabText = self.ui.data_tabs.tabText( ind )
            if tabText == tabName:
                return ind
        return -1

    def contextMenuEvent( self, event ):
        evPos     = event.pos()
        globalPos = self.mapToGlobal( evPos )
        tabBar    = self.ui.data_tabs.tabBar()
        tabPos    = tabBar.mapFromGlobal( globalPos )
        tabIndex  = tabBar.tabAt( tabPos )

        contextMenu   = QMenu(self)
        newAction     = contextMenu.addAction("New")
        renameAction  = contextMenu.addAction("Rename")
        deleteAction  = contextMenu.addAction("Delete")

        if tabIndex < 0:
            renameAction.setEnabled( False )
            deleteAction.setEnabled( False )

        action = contextMenu.exec_( globalPos )

        if action == newAction:
            self._newTabRequest()
        elif action == renameAction:
            self._renameTabRequest( tabIndex )
        elif action == deleteAction:
            favCode = self.ui.data_tabs.tabText( tabIndex )
            self.removeFavGrp.emit( favCode )

    def tabMoved(self):
        favOrder = []
        tabsSize = self.ui.data_tabs.count()
        for tabIndex in range(0, tabsSize):
            favCode = self.ui.data_tabs.tabText( tabIndex )
            favOrder.append( favCode )
        self.dataObject.reorderFavGroups( favOrder )

    def _newTabRequest( self ):
        newTitle = self._requestTabName( "Favs" )
        if len(newTitle) < 1:
            return
        self.addFavGrp.emit( newTitle )

    def _renameTabRequest( self, tabIndex ):
        if tabIndex < 0:
            return
        oldTitle = self.ui.data_tabs.tabText( tabIndex )
        newTitle = self._requestTabName(oldTitle)
        if not newTitle:
            # empty
            return
        self.renameFavGrp.emit( oldTitle, newTitle )

    def _requestTabName( self, currName ):
        newText, ok = QInputDialog.getText( self,
                                            "Rename Fav Group",
                                            "Fav Group name:",
                                            QLineEdit.Normal,
                                            currName )
        if ok and newText:
            # not empty
            return newText
        return ""
