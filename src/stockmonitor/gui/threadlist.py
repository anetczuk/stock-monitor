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
import threading

from PyQt5 import QtCore
from PyQt5.QtCore import Qt


_LOGGER = logging.getLogger(__name__)


class ThreadList():

    def __init__(self):
        self.threads = list()

    def append(self, thread: threading.Thread, startThread=False):
        if startThread:
            thread.start()
        self.threads.append( thread )

    def appendStart(self, thread: threading.Thread):
        self.append( thread, True )

    def start(self):
        for thr in self.threads:
            thr.start()

    def join(self):
        for thr in self.threads:
            thr.join()


## ============================================================


class ThreadWorker( QtCore.QObject ):

    finished = QtCore.pyqtSignal()

    def __init__(self, func, args=None, parent=None):
        super().__init__( None )
        if args is None:
            args = []
        self.func = func
        self.args = args

        self.thread = QtCore.QThread( parent )
        self.moveToThread( self.thread )
        self.thread.started.connect( self.processWorker, Qt.QueuedConnection )
        self.finished.connect( self.thread.quit )
        self.finished.connect( self.deleteLater )
        self.thread.finished.connect( self.thread.deleteLater )

    def start(self):
        self.thread.start()

    def wait(self):
        self.thread.wait()

    def processWorker(self):
#         _LOGGER.info("executing function: %s %s", self.func, self.args)
        if self.func is not None:
            self.func( *self.args )
#         _LOGGER.info("executing finished")
        _LOGGER.info( "work finished" )
        self.finished.emit()


class QThreadList( QtCore.QObject ):

    finished = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__( parent )
        self.threads = list()
        self.finishCounter = 0

    def appendFunction(self, function, args=None):
        worker = ThreadWorker( function, args, self )
        worker.thread.finished.connect( self._threadFinished )
        self.threads.append( worker )

    def start(self):
        _LOGGER.info( "starting threads" )
        for thr in self.threads:
            thr.start()

    def join(self):
        for thr in self.threads:
            thr.wait()

    def _threadFinished(self):
        #_LOGGER.info( "thread finished" )
        self.finishCounter += 1
        if self.finishCounter == len( self.threads ):
            _LOGGER.info( "all threads finished" )
            self.finished.emit()
