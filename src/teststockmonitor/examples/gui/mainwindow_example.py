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

from PyQt5.QtWidgets import QApplication

from stockdataaccess import logger
from stockdataaccess.dataaccess.worksheetdata import WorksheetStorageMock

from stockmonitor.datatypes.datatypes import MarkerEntry
from stockmonitor.gui.sigint import setup_interrupt_handling
from stockmonitor.gui.mainwindow import MainWindow

from teststockmonitor.data import get_data_path


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


parser = argparse.ArgumentParser(description='Stock Monitor Example')
parser.add_argument('-lud', '--loadUserData', action='store_const', const=True, default=False, help='Load user data' )
parser.add_argument('--minimized', action='store_const', const=True, default=False, help='Start minimized' )

args = parser.parse_args()


logFile = logger.get_logging_output_file()
logger.configure( logFile )

_LOGGER = logging.getLogger(__name__)


_LOGGER.debug( "Starting the application" )


app = QApplication(sys.argv)
app.setApplicationName("StockMonitor")
app.setOrganizationName("arnet")
app.setQuitOnLastWindowClosed( False )

setup_interrupt_handling()

window = MainWindow()
window.setWindowTitleSuffix( "Preview" )
window.disableSaving()
window.setWindowTitle( window.windowTitle() )
if args.loadUserData:
    window.loadData()
else:
    currentStock = window.data.gpwCurrentData

    def data_path():
        return get_data_path( "test_stock_data.html" )

    currentStock.dao.getDataPath = data_path           # type: ignore
    currentStock.dao.storage = WorksheetStorageMock()
    currentStock.dao.parseWorksheetFromFile( data_path() )

    window.data.addFav("abc", ["ALR"])
    window.data.addFav("abc", ["CDR"])

    window.data.wallet.addTransactionData( "CDR", 10, 300 )
    window.data.wallet.addTransactionData( "XXX", 10, 300 )
    window.data.wallet.addTransactionData( "ABC", 10, 300 )
#     window.data.wallet.addTransactionData( "AAA1", 300, 10 )
#     window.data.wallet.addTransactionData( "AAA2", 300, 10 )
#     window.data.wallet.addTransactionData( "AAA3", 300, 10 )
#     window.data.wallet.addTransactionData( "AAA4", 300, 10 )

    window.data.markers.addMarker( "ABC", 11, 22, MarkerEntry.OperationType.BUY )
    window.data.markers.addMarker( "XYZ", 33, 44, MarkerEntry.OperationType.BUY )
    window.data.markers.addMarker( "AAA1", 20, 100, MarkerEntry.OperationType.BUY )
    window.data.markers.addMarker( "AAA2",  5, 100, MarkerEntry.OperationType.BUY )
    window.data.markers.addMarker( "AAA3", 20, 100, MarkerEntry.OperationType.SELL, "red" )
    window.data.markers.addMarker( "AAA4",  5, 100, MarkerEntry.OperationType.SELL, "yellow" )

    window.data.notes["notes"] = "example note"
    window.data.notes["aaa note"] = "notes example"

window.loadSettings()
window.refreshView()

window.show()
# if args.minimized is True or window.appSettings.startMinimized is True:
#     ## starting minimized
#     pass
# else:
#     window.show()

exitCode = app.exec_()

if exitCode == 0:
    window.saveSettings()

sys.exit( exitCode )
