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

import os
import logging

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from stockmonitor.logger import get_logging_output_file
from stockmonitor.gui.appwindow import AppWindow

from .. import uiloader


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


_LOGGER = logging.getLogger(__name__)


class LogWidget( QtBaseClass ):           # type: ignore

    fileChanged   = pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.fileChanged.connect( self.updateLogView, QtCore.Qt.QueuedConnection )

        self.logFile = get_logging_output_file()

        ## prevents infinite feedback loop
        logging.getLogger('watchdog.observers.inotify_buffer').setLevel(logging.INFO)

        event_handler = PatternMatchingEventHandler( patterns=[self.logFile] )
        event_handler.on_any_event = self._logFileChanged

        dirPath = os.path.dirname( self.logFile )
        self.observer = Observer()
        self.observer.schedule( event_handler, path=dirPath, recursive=False )
        self.observer.start()

        self.updateLogView()

    def updateLogView(self):
        verticalBar = self.ui.textEdit.verticalScrollBar()
        vertValue = verticalBar.value()
        atBottom = vertValue == verticalBar.maximum()

        with open(self.logFile, "r") as myfile:
            fileText = myfile.read()
            self.ui.textEdit.setText( str(fileText) )

        if atBottom:
            verticalBar.setValue( verticalBar.maximum() )
        else:
            verticalBar.setValue( vertValue )

    # Override closeEvent, to intercept the window closing event
    def closeEvent(self, event):
        self.observer.stop()
        self.observer.join()
        super().closeEvent( event )
        self.close()

    def _logFileChanged(self, _):
        self.fileChanged.emit()


def create_window( parent=None ):
    logWindow = AppWindow( parent )
    widget = LogWidget( logWindow )
    logWindow.addWidget( widget )
    logWindow.show()
    return logWindow
