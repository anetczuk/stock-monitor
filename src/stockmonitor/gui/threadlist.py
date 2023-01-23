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

        self._workers = []
        self._stopped = False

    def workersNum(self):
        with self.workersMutex:
            return self._workersNum()

    @abc.abstractmethod
    def start(self):
        raise NotImplementedError('You need to define this method in derived class!')

    def stopExecution(self):
        with self.workersMutex:
            self._stopped = True

    def _workersNum(self):
        return len( self._workers )

    def _appendWorker(self, worker):
        with self.workersMutex:
            self._workers.append( worker )
        return worker

    def _workerFinished(self):
        with self.workersMutex:
            self.finishCounter += 1
            workersSize = self._workersNum()
            if self.logging:
    #             worker = self.sender()                    ## 'self.sender()' is not reliable
                _LOGGER.info( "%s: worker finished %s / %s", id(self), self.finishCounter, workersSize )
                flush_handlers( _LOGGER )
            if self.finishCounter == workersSize:
                self._computingFinished()

    def _computingFinished(self):
        self.finishCounter = 0
        self._workers.clear()

        if self._stopped:
            _LOGGER.info( "%s: threads execution stopped, 'finish' signal blocked", id(self) )
            return

        if self.logging:
            endTime  = datetime.datetime.now()
            diffTime = endTime - self.startTime
            _LOGGER.info( "%s: all workers finished, computation time: %s", id(self), diffTime )
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
            _LOGGER.debug( "worker[%s] started", id(self) )
            try:
                self.command.execute()
            # pylint: disable=W0703
            except Exception:
                _LOGGER.exception( "worker[%s] terminated", id(self) )
            finally:
                self.pool._workerFinished()


    def __init__(self, parent=None, logs=True):
        super().__init__( parent, logs )

        self.pool = QtCore.QThreadPool.globalInstance()

    def deleteOnFinish(self):
        self.finished.connect( self.deleteLater )
#         self.finished.connect( self.deleteLater, Qt.QueuedConnection )

    ## accepts list of pairs
    def start(self, call_list):
        if self.logging:
            _LOGGER.info( "%s: starting workers", id(self) )
            self.startTime = datetime.datetime.now()

        workers_list = []
        for call_pair in call_list:
            func, args = call_pair
            command = CommandObject( func, args )
            worker = ThreadPoolList.Worker( command, self )
            self._appendWorker( worker )
            workers_list.append( worker )

        if self.logging:
            _LOGGER.info( "%s: executing threads, stack size: %s max: %s", id(self), self.pool.activeThreadCount(), self.pool.maxThreadCount() )

        threads_count = len(workers_list)
        thread_num    = 0
        for worker in workers_list:
            thread_num += 1
            _LOGGER.debug( "%s: starting worker[%s] %s / %s", id(self), id(worker), thread_num, threads_count )
            executed = self.pool.start( worker )
            if executed is False:
                _LOGGER.debug( "%s: worker[%s] added to queue, threads limit: %s", id(self), id(worker), self.pool.maxThreadCount() )

    @staticmethod
    def calculate( parent, function, args=None ):
        pool = ThreadPoolList( parent )
        pool.deleteOnFinish()
        call_list = [ (function, args) ]
        pool.start( call_list )


## ====================================================================


##
##
##
class SerialList( AbstractWorkerList ):

    def __init__(self, parent=None, logs=True):
        super().__init__( parent, logs )

    def start(self, call_list):
        if self.logging:
            _LOGGER.info( "starting workers" )
            self.startTime = datetime.datetime.now()

        commands_list = []
        for call_pair in call_list:
            func, args = call_pair
            command = CommandObject( func, args )
            self._appendWorker( command )
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


## ========================================================


def get_threading_list_class():
    """Return threading list class (factory function)."""
    return ThreadPoolList
    # return SerialList


def calculate( parent, function, args=None ):
    if _SINGLE_THREADED is False:
        ThreadPoolList.calculate(parent, function, args)
    else:
        command = CommandObject( function, args )
        command.execute()
