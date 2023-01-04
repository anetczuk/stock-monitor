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

from PyQt5.QtWidgets import QApplication

from stockdataaccess import logger
from stockmonitor.gui.dataobject import DataObject
from stockmonitor.gui.sigint import setup_interrupt_handling
from stockmonitor.gui.widget.transactionswidget import TransactionsWidget


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


logFile = logger.get_logging_output_file()
logger.configure( logFile )

_LOGGER = logging.getLogger(__name__)


app = QApplication(sys.argv)
app.setApplicationName("StockMonitor")
app.setOrganizationName("arnet")

dataObject = DataObject()
dataObject.loadDownloadedStocks()
dataObject.wallet.add( "EAT", 111, 11.1 )
dataObject.wallet.add( "ALR", 222, 22.2 )
dataObject.wallet.add( "CDR", 333, 33.3 )
dataObject.wallet.add( "YYY", 444, 44.4 )

setup_interrupt_handling()

widget = TransactionsWidget()
widget.resize( 1024, 768 )
widget.connectData(dataObject)
widget.show()

sys.exit( app.exec_() )
