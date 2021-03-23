# MIT License
#
# Copyright (c) 2021 Arkadiusz Netczuk <dev.arnet@gmail.com>
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

import os
import logging

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from stockmonitor.logger import get_logging_output_file
from stockmonitor.gui.appwindow import AppWindow

from .. import uiloader


_LOGGER = logging.getLogger(__name__)


class AutoScrollTextEdit( QtWidgets.QTextEdit ):

    switchAutoScroll = pyqtSignal( bool )

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.autoScroll = True
        self.setAutoScroll( False )

        self.setLineWrapMode( QtWidgets.QTextEdit.NoWrap )

        verticalBar = self.verticalScrollBar()
        verticalBar.rangeChanged.connect( self._scrollRangeChanged )
        verticalBar.valueChanged.connect( self._scrollValueChanged )

    def setAutoScroll( self, state: bool ):
        if self.autoScroll == state:
            return
        self.autoScroll = state
        if self.autoScroll:
            verticalBar = self.verticalScrollBar()
            verticalBar.setEnabled( False )
            self.scrollDown()
        else:
            verticalBar = self.verticalScrollBar()
            verticalBar.setEnabled( True )

    def setContent( self, content: str ):
        verticalBar = self.verticalScrollBar()
        currPos = verticalBar.value()
#         print( "setContent", "val:", currPos )

        cursor = self.textCursor()
        pos = cursor.position()

        self.setPlainText( content )

        cursor = self.textCursor()
        cursor.setPosition( pos )
        self.setTextCursor( cursor )

        if self.autoScroll is False:
            verticalBar.setValue( currPos )

    def scrollDown(self):
        verticalBar = self.verticalScrollBar()
        verticalBar.triggerAction( QtWidgets.QAbstractSlider.SliderToMaximum )

    def keyPressEvent(self, event):
        if self.autoScroll:
            moved = self._isMoveUp( event )
            if moved:
                self.switchAutoScroll.emit( False )
            super().keyPressEvent( event )
            return

        moved = self._isMoveDown( event )
        if not moved:
            ## not moved down -- regular behaviour
            super().keyPressEvent( event )
            return

        ## moved down
        super().keyPressEvent( event )
        self._handlePositionChange()

    def _isMoveUp(self, event):
        if event.key() == QtCore.Qt.Key_Up:
            return True
        if event.key() == QtCore.Qt.Key_PageUp:
            return True
        if (event.modifiers() & QtCore.Qt.ControlModifier) and event.key() == QtCore.Qt.Key_Home:
            return True
        return False

    def _isMoveDown(self, event):
        if event.key() == QtCore.Qt.Key_Down:
            return True
        if event.key() == QtCore.Qt.Key_PageDown:
            return True
        if (event.modifiers() & QtCore.Qt.ControlModifier) and event.key() == QtCore.Qt.Key_End:
            return True
        return False

    def wheelEvent(self, event):
        scrollDirection = event.angleDelta().y()
        if scrollDirection > 0:
            ## scrolling up
            if self.autoScroll:
                self.switchAutoScroll.emit( False )
            super().wheelEvent( event )
            return

        ## scrolling down
        super().wheelEvent( event )
        self._handlePositionChange()

    def _handlePositionChange( self ):
        verticalBar = self.verticalScrollBar()
        currValue = verticalBar.value()
        if verticalBar.maximum() - currValue < 10:
            ## did reach the bottom
            self.switchAutoScroll.emit( True )

    def _scrollRangeChanged(self, _, maxVal):
#     def _scrollRangeChanged(self, _, maxVal):
        verticalBar = self.verticalScrollBar()
#         print( "_scrollRangeChanged", "min:", minVal, "max:", maxVal, "val:", verticalBar.value() )
        if self.autoScroll:
            verticalBar.setValue( maxVal )

    def _scrollValueChanged(self, value):
        verticalBar = self.verticalScrollBar()
#         print( "_scrollValueChanged", "val:", value, "max:", verticalBar.maximum() )
        if self.autoScroll:
            if value != verticalBar.maximum():
                verticalBar.setValue( verticalBar.maximum() )


## ======================================================================


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


class LogWidget( QtBaseClass ):           # type: ignore

    fileChanged   = pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.fileChanged.connect( self._fileChanged, QtCore.Qt.QueuedConnection )
        self.ui.autoScrollCB.stateChanged.connect( self._autoScrollChanged )
        self.ui.autoScrollCB.setChecked( True )

        self.ui.splitByThredCB.stateChanged.connect( self._splitThreadsChanged )
#         self.ui.splitByThredCB.setChecked( True )

        self.logFile = get_logging_output_file()

        ## prevents infinite feedback loop
        logging.getLogger('watchdog.observers.inotify_buffer').setLevel(logging.INFO)

        event_handler = PatternMatchingEventHandler( patterns=[self.logFile] )
        event_handler.on_any_event = self._logFileCallback

        dirPath = os.path.dirname( self.logFile )
        self.observer = Observer()
        self.observer.schedule( event_handler, path=dirPath, recursive=False )

        self.updateLogView()
        self.observer.start()

    def updateLogView(self):
        ## method can be run from different threads
        ## call method through Qt event queue to prevent
        ## concurrent access control
        QtCore.QTimer.singleShot( 1, self._updateText )

    def scrollDown(self):
        layoutItems = self.ui.logLayout.count()
        for i in range(0, layoutItems):
            itemWidget = self.ui.logLayout.itemAt( i ).widget()
            if itemWidget is None:
                continue
            itemWidget.scrollDown()

    def _updateText(self):
        if self.ui.splitByThredCB.isChecked() is False:
            with open(self.logFile, "r") as myfile:
                fileText = myfile.read()
                content = str(fileText)
                textEdit = self._getTextEdit( "full" )
                textEdit.setContent( content )
            return

        threadsDict = {}

        with open(self.logFile, "r") as myfile:
            linesContent = myfile.readlines()
            recentThread = None
            for line in linesContent:
                fields = line.split()

                threadName = "full"
                threadLines = threadsDict.get( threadName, list() )
                threadLines.append( line )
                threadsDict[ threadName ] = threadLines

                if len(fields) > 3:
                    recentThread = fields[3]

                if recentThread is None:
                    continue

                threadLines = threadsDict.get( recentThread, list() )
                threadLines.append( line )
                threadsDict[ recentThread ] = threadLines

        for key, contentList in threadsDict.items():
            textEdit = self._getTextEdit( key )
            content = "".join( contentList )            ## newline char is in the end of each item of list (line)
            textEdit.setContent( content )

#         pprint( threadsDict )
#         print( threadsDict.keys() )

    def _autoScrollChanged(self):
        newState = self.ui.autoScrollCB.isChecked()
        layoutItems = self.ui.logLayout.count()
        for i in range(0, layoutItems):
            itemWidget = self.ui.logLayout.itemAt( i ).widget()
            if itemWidget is None:
                continue
            itemWidget.setAutoScroll( newState )

    def _splitThreadsChanged(self):
        self._clearTextWidgets()
        self.updateLogView()

    # Override closeEvent, to intercept the window closing event
    def closeEvent(self, event):
        self.observer.stop()
        self.observer.join()
        self.observer = None
        super().closeEvent( event )
        self.close()

    def _logFileCallback(self, _):
        if self.observer is None:
            ## window closed -- ignore
            return
        self.fileChanged.emit()

    def _fileChanged(self):
        self.updateLogView()

    def _clearTextWidgets(self):
        textLayout = self.ui.logLayout
        item = textLayout.takeAt( 0 )
        while item is not None:
            item.widget().deleteLater()
            del item
            item = textLayout.takeAt( 0 )

    def _getTextEdit(self, name):
        layoutItems = self.ui.logLayout.count()
        for i in range(0, layoutItems):
            itemWidget = self.ui.logLayout.itemAt( i ).widget()
            if itemWidget is None:
                continue
            if itemWidget.objectName() == name:
                return itemWidget

        newTextEdit = AutoScrollTextEdit( self )
        newTextEdit.switchAutoScroll.connect( self.ui.autoScrollCB.setChecked )
        newTextEdit.setObjectName( name )
        newState = self.ui.autoScrollCB.isChecked()
        newTextEdit.setAutoScroll( newState )
        self.ui.logLayout.addWidget( newTextEdit )
        return newTextEdit


def create_window( parent=None ):
    logWindow = AppWindow( parent )
    newTitle = AppWindow.appTitle + " Log"
    logWindow.setWindowTitle( newTitle )

    widget = LogWidget( logWindow )
    logWindow.addWidget( widget )
    logWindow.move( 0, 0 )

    deskRec = QApplication.desktop().screenGeometry()
    deskWidth = deskRec.width()
    logWindow.resize( deskWidth, 600 )
    logWindow.show()
    return logWindow
