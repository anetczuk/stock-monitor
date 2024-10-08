#!/usr/bin/env python3
#
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

try:
    ## following import success only when file is directly executed from command line
    ## otherwise will throw exception when executing as parameter for "python -m"
    # pylint: disable=W0611
    import __init__
except ImportError:
    ## when import fails then it means that the script was executed indirectly
    ## in this case __init__ is already loaded
    pass

import sys
import logging
import argparse

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication

from stockdataaccess import logger
from stockmonitor.gui.sigint import setup_interrupt_handling
from stockmonitor.gui.widget.logwidget import create_window
# from stockmonitor.gui.resources import get_root_path
# from stockmonitor.gui.utils import render_to_pixmap


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


parser = argparse.ArgumentParser(description='Work Log Example')
# parser.add_argument('-lud', '--loadUserData', action='store_const', const=True, default=False, help='Load user data' )
# parser.add_argument('--minimized', action='store_const', const=True, default=False, help='Start minimized' )

args = parser.parse_args()


logFile = logger.get_logging_output_file()
logger.configure( logFile )

_LOGGER = logging.getLogger(__name__)


_LOGGER.debug( "Starting the application" )


app = QApplication(sys.argv)
app.setApplicationName("WorkLog")
app.setOrganizationName("arnet")
app.setQuitOnLastWindowClosed( True )

setup_interrupt_handling()

window = create_window()


def timer_tick():
    _LOGGER.info( "Timer tick" )


tickTimer = QtCore.QTimer( window )
tickTimer.timeout.connect( timer_tick )             # type: ignore
tickTimer.start( 8000 )                             ## every second


# window.setWindowTitleSuffix( "Preview" )
# window.setWindowTitle( window.windowTitle() )

exitCode = app.exec_()
sys.exit( exitCode )
