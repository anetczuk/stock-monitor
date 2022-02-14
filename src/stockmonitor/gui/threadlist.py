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
import datetime
import abc

from multiprocessing import Process

from PyQt5 import QtCore
from PyQt5.QtCore import Qt


_LOGGER = logging.getLogger(__name__)


class ThreadList():

    def __init__(self):
        self.threads = []

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


class BaseWorker( QtCore.QObject ):

    finished = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__( None )

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

    @abc.abstractmethod
    def processWorker(self):
        raise NotImplementedError('You need to define this method in derived class!')


class ThreadWorker( BaseWorker ):

    def __init__(self, func, args=None, parent=None, logs=True):
        super().__init__( parent )
        if args is None:
            args = []
        self.func = func
        self.args = args
        self.logging = logs

    def processWorker(self):
#         _LOGGER.info("executing function: %s %s", self.func, self.args)
        try:
            if self.func is not None:
                self.func( *self.args )
            if self.logging:
        #         _LOGGER.info("executing finished")
                _LOGGER.info( "work finished" )
        # pylint: disable=W0703
        except Exception:
            _LOGGER.exception("work terminated" )
        finally:
            self.finished.emit()


class QThreadList( QtCore.QObject ):

    finished = QtCore.pyqtSignal()

    def __init__(self, parent=None, logs=True):
        super().__init__( parent )
        self.threads = []
        self.finishCounter = 0
        self.logging = logs

    def appendFunction(self, function, args=None):
        worker = ThreadWorker( function, args, self, self.logging )
        worker.thread.finished.connect( self._threadFinished )
        self.threads.append( worker )

#     def map(self, func, argsList):
#         for arg in argsList:
#             self.appendFunction( func, arg )

    def start(self):
        if self.logging:
            _LOGGER.info( "starting threads" )
        for thr in self.threads:
            thr.start()

    def join(self):
        for thr in self.threads:
            thr.wait()

    def _threadFinished(self):
        self.finishCounter += 1
        if self.finishCounter == len( self.threads ):
            self._computingFinished()

    def _computingFinished(self):
        if self.logging:
            _LOGGER.info( "all threads finished" )
        self.finished.emit()


class QThreadMeasuredList( QThreadList ):

    def __init__(self, parent=None, logs=True):
        super().__init__( parent, logs )
        self.startTime = None

    def deleteOnFinish(self):
        self.finished.connect( self.deleteLater )

    def start(self):
        self.startTime = datetime.datetime.now()
        super().start()

    def _computingFinished(self):
        endTime = datetime.datetime.now()
        diffTime = endTime - self.startTime
        _LOGGER.info( "computation time: %s", diffTime )
        super()._computingFinished()

    @staticmethod
    def calculate( parent, function, args=None ):
        threads = QThreadMeasuredList( parent )
        threads.deleteOnFinish()
        threads.appendFunction( function, args )
        threads.start()


## ====================================================================


class SerialList( QtCore.QObject ):
    """List without multithreading."""

    finished = QtCore.pyqtSignal()

    def __init__(self, parent=None, logs=True):
        super().__init__( parent )
        self.commandsList = []
        self.logging = logs
        self.startTime = None

    def appendFunction(self, function, args=None):
        self.commandsList.append( (function, args) )

    def start(self):
        self.startTime = datetime.datetime.now()
        if self.logging:
            _LOGGER.info( "starting computation" )
        for func, args in self.commandsList:
            if func is not None:
                func( *args )
        self.finished.emit()
        endTime = datetime.datetime.now()
        diffTime = endTime - self.startTime
        if self.logging:
            _LOGGER.info( "computation time: %s", diffTime )

    def join(self):
        pass


## ====================================================================


class ProcessWorker( BaseWorker ):

    def __init__(self, func, args=None, parent=None):
        super().__init__( parent )
        if args is None:
            args = []
        self.func = func
        self.args = args

    def processWorker(self):
#         _LOGGER.info("executing function: %s %s", self.func, self.args)
        try:
            process = Process( target=self.func, args=self.args )
            process.start()
            process.join()
    #         _LOGGER.info("executing finished")
            _LOGGER.info( "work finished" )
        # pylint: disable=W0703
        except Exception:
            _LOGGER.exception("work terminated" )
        finally:
            self.finished.emit()


class ProcessList( QtCore.QObject ):

    finished = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__( parent )
        self.threads = []
        self.finishCounter = 0
        self.startTime = None

    def appendFunction(self, function, args=None):
        worker = ProcessWorker( function, args, self )
        worker.thread.finished.connect( self._threadFinished )
        self.threads.append( worker )

    def start(self):
        _LOGGER.info( "starting processes" )
        self.startTime = datetime.datetime.now()
        for thr in self.threads:
            thr.start()

    def join(self):
        for thr in self.threads:
            thr.wait()

    def _threadFinished(self):
        #_LOGGER.info( "process finished" )
        self.finishCounter += 1
        if self.finishCounter == len( self.threads ):
            self._computingFinished()

    def _computingFinished(self):
        _LOGGER.info( "all processes finished" )
        self.finished.emit()
        endTime = datetime.datetime.now()
        diffTime = endTime - self.startTime
        _LOGGER.info( "computation time: %s", diffTime )


## ========================================================


def get_threading_list():
    """Return threading list class (factory function)."""
    return QThreadMeasuredList
#    return SerialList
