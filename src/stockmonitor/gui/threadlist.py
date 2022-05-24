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

from PyQt5 import QtCore
from PyQt5.QtCore import Qt

from stockmonitor.logger import flush_handlers


_LOGGER = logging.getLogger(__name__)


class ThreadingList():

    def __init__(self):
        self.threads = []

    def append(self, thread: threading.Thread, startThread=False):
        if startThread:
            thread.start()
        self.threads.append( thread )

    def appendFunction(self, function, args=None, startThread=False):
        thread = threading.Thread( target=function, args=args )
        self.append( thread, startThread )

    def start(self):
        for thr in self.threads:
            thr.start()

    def join(self):
        for thr in self.threads:
            thr.join()


## ============================================================


class CommandObject:
    
    def __init__(self, func, args=None):
        if args is None:
            args = []
        self.func = func
        self.args = args

    def execute(self):
        if self.func is not None:
            self.func( *self.args )


class AbstractWorker( QtCore.QObject ):

    workerFinished = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__( parent )

#     def __del__(self):
#         _LOGGER.info( "object destructor: %s, thread: %s", self, self.threadName )
#         flush_handlers( _LOGGER )

    @abc.abstractmethod
    def start(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def wait(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def info(self):
        raise NotImplementedError('You need to define this method in derived class!')


##
##
##
class AbstractWorkerList( QtCore.QObject ):

    finished = QtCore.pyqtSignal()

    def __init__(self, parent=None, logs=True):
        super().__init__( parent )
        self.workersMutex = threading.Lock()
        self.finishCounter = 0
        self.startTime = None
        self.logging = logs

    @abc.abstractmethod
    def workersNum(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def start(self):
        raise NotImplementedError('You need to define this method in derived class!')

    def _workerFinished(self):
        with self.workersMutex:
            self.finishCounter += 1
            workersSize = self.workersNum()
            if self.logging:
    #             worker = self.sender()                    ## 'self.sender()' is not reliable
                _LOGGER.info( "worker finished %s / %s", self.finishCounter, workersSize )
                flush_handlers( _LOGGER )
            if self.finishCounter == workersSize:
                self._computingFinished()

    def _computingFinished(self):
        if self.logging:
            endTime  = datetime.datetime.now()
            diffTime = endTime - self.startTime
            _LOGGER.info( "all workers finished, computation time: %s", diffTime )
        self.finished.emit()


## ====================================================================


##
##
##
class ThreadPoolList( AbstractWorkerList ):

    class Worker( QtCore.QRunnable ):

        def __init__( self, command, pool: 'ThreadPoolList' ):
            super().__init__()
            self.command = command
            self.pool = pool

        def run(self):
            try:
                self.command.execute()
            # pylint: disable=W0703
            except Exception:
                _LOGGER.exception( "work terminated" )
            finally:
                self.pool._workerFinished()


    def __init__(self, parent=None, logs=True):
        super().__init__( parent, logs )
        
        self.pool = QtCore.QThreadPool.globalInstance()
        self._workers = []

    def deleteOnFinish(self):
        self.finished.connect( self.deleteLater )
#         self.finished.connect( self.deleteLater, Qt.QueuedConnection )

    def appendFunction(self, function, args=None):
        command = CommandObject( function, args )
        worker = ThreadPoolList.Worker( command, self )
        self._workers.append( worker )

    def workersNum(self):
        return len( self._workers )

    def start(self):
        if self.logging:
            _LOGGER.info( "starting workers" )
            self.startTime = datetime.datetime.now()
        for worker in self._workers:
            self.pool.start( worker )

    @staticmethod
    def calculate( parent, function, args=None ):
        pool = ThreadPoolList( parent )
        pool.deleteOnFinish()
        pool.appendFunction( function, args )
        pool.start()


## ====================================================================


##
##
##
class SerialList( AbstractWorkerList ):

    def __init__(self, parent=None, logs=True):
        super().__init__( parent, logs )
        self._commands = []

    def workersNum(self):
        return len( self._commands )

    def appendFunction(self, function, args=None):
        command = CommandObject( function, args )
        self._commands.append( command )

    def start(self):
        if self.logging:
            _LOGGER.info( "starting workers" )
            self.startTime = datetime.datetime.now()

        for command in self._commands:
            try:
                command.execute()
            # pylint: disable=W0703
            except Exception:
                _LOGGER.exception( "work terminated" )
            finally:
                if self.logging:
                    _LOGGER.info( "work finished" )
                self._workerFinished()


## ========================================================


def get_threading_list():
    """Return threading list class (factory function)."""
    return ThreadPoolList
#     return SerialList


def calculate( parent, function, args=None ):
    ThreadPoolList.calculate(parent, function, args)
