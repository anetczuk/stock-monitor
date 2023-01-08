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

from stockdataaccess.logger import flush_handlers


_LOGGER = logging.getLogger(__name__)


_SINGLE_THREADED = False
# _SINGLE_THREADED = True


class ThreadingList():

    def __init__(self):
        self.threads = []

#     def append(self, thread: threading.Thread, startThread=False):
#         if startThread:
#             thread.start()
#         self.threads.append( thread )

    def start(self, call_list):
        threads_list = []
        for call_pair in call_list:
            func, args = call_pair
            thread = self._appendFunction( func, args )
            threads_list.append( thread )

        for thread in threads_list:    
            thread.start()

    def join(self):
        for thr in self.threads:
            thr.join()

    def _appendFunction(self, function, args=None, startThread=False):
        thread = threading.Thread( target=function, args=args )
        self.append( thread, startThread )
        return thread


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
        self._stopped = False

    @abc.abstractmethod
    def workersNum(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def start(self):
        raise NotImplementedError('You need to define this method in derived class!')

    def stopExecution(self):
        with self.workersMutex:
            self._stopped = True

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
        if self._stopped:
            _LOGGER.info( "threads execution stopped, 'finish' signal blocked" )
            return

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

    def workersNum(self):
        return len( self._workers )

    def start(self, call_list):
        if self.logging:
            _LOGGER.info( "starting workers" )
            self.startTime = datetime.datetime.now()

        workers_list = []
        for call_pair in call_list:
            func, args = call_pair
            worker = self._appendFunction( func, args )
            workers_list.append( worker )

        for worker in workers_list:
            self.pool.start( worker )

    def _appendFunction(self, function, args=None):
        command = CommandObject( function, args )
        worker = ThreadPoolList.Worker( command, self )
        self._workers.append( worker )
        return worker

    @staticmethod
    def calculate( parent, function, args=None ):
        pool = ThreadPoolList( parent )
        pool.deleteOnFinish()
        pool.start( [function, args] )


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

    def start(self, call_list):
        if self.logging:
            _LOGGER.info( "starting workers" )
            self.startTime = datetime.datetime.now()

        commands_list = []
        for call_pair in call_list:
            func, args = call_pair
            command = self._appendFunction( func, args )
            commands_list.append( command )

        for command in commands_list:
            try:
                command.execute()
            # pylint: disable=W0703
            except Exception:
                _LOGGER.exception( "work terminated" )
            finally:
                if self.logging:
                    _LOGGER.info( "work finished" )
                self._workerFinished()

    def _appendFunction(self, function, args=None):
        command = CommandObject( function, args )
        self._commands.append( command )
        return command


## ========================================================


def get_threading_list_class():
    """Return threading list class (factory function)."""
    return ThreadPoolList
#     return SerialList


def calculate( parent, function, args=None ):
    if _SINGLE_THREADED is False:
        ThreadPoolList.calculate(parent, function, args)
    else:
        command = CommandObject( function, args )
        command.execute()
