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

import random

import sys
import logging
import datetime
from typing import Dict

import pandas

from PyQt5.QtWidgets import QApplication

from stockdataaccess import logger
from stockmonitor.gui.sigint import setup_interrupt_handling
from stockmonitor.gui.widget.mpl.candlestickchart import PriceCandleStickChart, PriceValueCandleStickChart


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


logFile = logger.get_logging_output_file()
logger.configure( logFile )

_LOGGER = logging.getLogger(__name__)


app = QApplication(sys.argv)
app.setApplicationName("StockMonitor")
app.setOrganizationName("arnet")

# xdata = [ datetime.datetime.fromtimestamp( 100000 ), datetime.datetime.fromtimestamp( 200000 ),
#           datetime.datetime.fromtimestamp( 300000 ), datetime.datetime.fromtimestamp( 400000 ),
#           datetime.datetime.fromtimestamp( 500000 ) ]

start_date = datetime.datetime.now() - datetime.timedelta(days=20)
xdata = []
# for _ in range(0, 5):
#     xdata.append( start_date )
#     start_date += datetime.timedelta( days=1 )
# print( "xxx:", xdata )

# open_data    = [ 1, 10, 5, 4, 1 ]
# high_data    = [ 5, 11, 5, 5, 8 ]
# low_data     = [ 1,  3, 2, 2, 1 ]
# volumen_data = [ 5,  4, 2, 3, 7 ]
#
# frame = { 'Open': open_data, 'High': high_data, 'Low': low_data, 'Close': volumen_data, 'Volume': volumen_data }
frame: Dict = { 'Open': [], 'High': [], 'Low': [], 'Close': [], 'Volume': [] }

random.seed( 10 )

for i in range(0, 20):
    xdata.append( start_date )
    start_date += datetime.timedelta( days=random.choice( [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2] ) )
#     start_date += datetime.timedelta( days=1 )
    vopen = random.randrange( 10 )
    vclose = vopen + random.randint( -5, 5 )
    vmin = min( vopen, vclose ) - random.randrange( 3 )
    vmax = max( vopen, vclose ) + random.randrange( 3 )
    volume = random.randrange( 10 ) + 1

    frame[ "Open" ].append( vopen )
    frame[ "High" ].append( vclose )
    frame[ "Low" ].append( vmin )
    frame[ "Close" ].append( vmax )
    frame[ "Volume" ].append( volume )

dataframe = pandas.DataFrame( frame )
dataframe.index = pandas.DatetimeIndex( xdata )

setup_interrupt_handling()


widget = PriceCandleStickChart()
widget.resize( 1024, 768 )
widget.addPriceCandles( dataframe )
widget.show()

widget = PriceValueCandleStickChart()
widget.generateMosaicItems( 4 )
widget.resize( 1024, 768 )
widget.addPriceCandles( dataframe )
widget.show()

sys.exit( app.exec_() )
