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

        self.ui.data_tabs.clear()
        self.addTab( "Favs" )

    def connectData(self, dataObject):
        self.dataObject = dataObject
        self.dataObject.stockDataChanged.connect( self.updateView )
        self.dataObject.favsChanged.connect( self.updateView )
        self.updateView()

    def updateView(self):
        if self.dataObject is None:
            _LOGGER.warning("unable to update view")
            self.ui.data_tabs.clear()
            return
        favsObj = self.dataObject.favs
        dataDict = favsObj.favs
        favKeys = dataDict.keys()
        keysNum = len(favKeys)
        tabsNum = self.ui.data_tabs.count()
        if keysNum > tabsNum:
            for i in range(tabsNum, keysNum):
                self.addTab( str(i) )
        elif tabsNum > keysNum:
            for i in range(keysNum, tabsNum):
                self.ui.data_tabs.removeTab( keysNum )
        i = -1
        for key in favKeys:
            i += 1
            page = self.ui.data_tabs.widget( i )
            page.setData( self.dataObject, key )

    def addTab(self, favGroup):
        pageWidget = SinglePageWidget(self)
        pageWidget.setData( self.dataObject, favGroup )
        self.ui.data_tabs.addTab( pageWidget, favGroup )

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
            noteTitle = self.ui.data_tabs.tabText( tabIndex )
            self.removeFavGrp.emit( noteTitle )

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
