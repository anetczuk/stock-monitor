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
class WorkerList( QtCore.QObject ):

    finished = QtCore.pyqtSignal()

    def __init__(self, parent=None, logs=True):
        super().__init__( parent )
        self._workers: AbstractWorker = []
        self.workersMutex = threading.Lock()
        self.finishCounter = 0
        self.startTime = None
        self.logging = logs

#     def __del__(self):
#         _LOGGER.info( "object destructor: %s", self )
#         flush_handlers( _LOGGER )

#     def map(self, func, argsList):
#         for arg in argsList:
#             self.appendFunction( func, arg )

    def start(self):
        if self.logging:
            _LOGGER.info( "starting workers" )
            self.startTime = datetime.datetime.now()
        for thr in self._workers:
            thr.start()

    def join(self):
        for thr in self._workers:
            thr.wait()

    def _appendWorker(self, worker: AbstractWorker ):
        worker.workerFinished.connect( self._workerFinished )
        self._workers.append( worker )

    def _workerFinished(self):
        with self.workersMutex:
            self.finishCounter += 1
            threadsSize = len( self._workers )
            if self.logging:
    #             worker = self.sender()                    ## 'self.sender()' is not reliable
                _LOGGER.info( "worker finished %s / %s", self.finishCounter, threadsSize )
                flush_handlers( _LOGGER )
            if self.finishCounter == threadsSize:
                self._computingFinished()

    def _computingFinished(self):
        if self.logging:
            endTime  = datetime.datetime.now()
            diffTime = endTime - self.startTime
            _LOGGER.info( "all workers finished, computation time: %s", diffTime )

        self.finished.emit()


### =========================================================================


class ThreadWorker( AbstractWorker ):
    """ Execute work in separated thread."""

    def __init__(self, func, args=None, parent=None, logs=True):
        super().__init__( None )
        self.command = CommandObject( func, args )
        self.logging = logs

        self.threadName = None

        self.thread = QtCore.QThread( parent )
        self.moveToThread( self.thread )            ## thread become parent of object

        self.thread.started.connect( self._processtWorker )
#        self.workerFinished.connect( self.thread.quit )
        self.thread.finished.connect( self.workerFinished )

    def start(self):
        self.thread.start()

    def wait(self):
        self.thread.wait()

    def info(self):
        return self.threadName

    def _processtWorker(self):        
        try:
            self.threadName = threading.current_thread().name
            self.command.execute()
        # pylint: disable=W0703
        except Exception:
            _LOGGER.exception( "work terminated" )
        finally:
            if self.logging:
                _LOGGER.info( "work finished" )
            self.thread.quit()


##
##
##
class ThreadList( WorkerList ):

    def __init__(self, parent=None, logs=True):
        super().__init__( parent, logs )

    def appendFunction(self, function, args=None):
        worker = ThreadWorker( function, args, self, False )
        self._appendWorker( worker )

    def deleteOnFinish(self):
        self.finished.connect( self.deleteLater )

    @staticmethod
    def calculate( parent, function, args=None ):
        threads = ThreadList( parent )
        threads.deleteOnFinish()
        threads.appendFunction( function, args )
        threads.start()


## ====================================================================


class SerialWorker( AbstractWorker ):

    def __init__(self, func, args=None, parent=None, logs=True):
        super().__init__( parent )
        self.command = CommandObject( func, args )
        self.logging = logs

    def start(self):
        try:
            self.command.execute()
        # pylint: disable=W0703
        except Exception:
            _LOGGER.exception( "work terminated" )
        finally:
            if self.logging:
                _LOGGER.info( "work finished" )
            self.workerFinished.emit()

    def wait(self):
        ## do nothing
        pass

    def info(self):
        return str(self)


##
##
##
class SerialList( WorkerList ):

    def __init__(self, parent=None, logs=True):
        super().__init__( parent, logs )

    def appendFunction(self, function, args=None):
        worker = SerialWorker( function, args, self, False )
        self._appendWorker( worker )
                        

## ========================================================


def get_threading_list():
    """Return threading list class (factory function)."""
    return ThreadList
#     return SerialList
