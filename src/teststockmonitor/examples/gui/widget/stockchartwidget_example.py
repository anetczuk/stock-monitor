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

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication

from stockdataaccess import logger
from stockdataaccess.dataaccess.gpw.gpwintradaydata import GpwCurrentStockIntradayData
from stockdataaccess.dataaccess.worksheetdata import WorksheetStorageMock

from stockmonitor.gui.dataobject import DataObject
from stockmonitor.gui.sigint import setup_interrupt_handling
from stockmonitor.gui.widget.stockchartwidget import create_window
from stockmonitor.gui.resources import get_root_path
from stockmonitor.gui.utils import render_to_pixmap

from teststockmonitor.data import get_data_path


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


def prepare_dataobject():
    data = DataObject()
    dataAccess = GpwCurrentStockIntradayData( "PLOPTTC00011" )

    def data_path():
        return get_data_path( "cdr.chart.04-09.txt" )

    dataAccess.dao.getDataPath = data_path                       # type: ignore
    dataAccess.dao.downloadData = lambda filePath: None          ## empty lambda function
    dataAccess.dao.storage = WorksheetStorageMock()

#     data.gpwStockIntradayData.set( "PLOPTTC00011", dataAccess )
#     data.gpwStockIntradayData.set( "CRD", dataAccess )
    return data


logFile = logger.get_logging_output_file()
logger.configure( logFile )

_LOGGER = logging.getLogger(__name__)


app = QApplication(sys.argv)
app.setApplicationName("StockMonitor")
app.setOrganizationName("arnet")

setup_interrupt_handling()

dataObject = prepare_dataobject()

widget = create_window( dataObject, "CDR" )
widget.resize( 1024, 768 )


def make_screen():
    _LOGGER.info("making screenshot")
    root_path = get_root_path()
    render_to_pixmap( widget, root_path + "/tmp/stockchartwindow-big.png" )


QtCore.QTimer.singleShot(3000, make_screen)

sys.exit( app.exec_() )
