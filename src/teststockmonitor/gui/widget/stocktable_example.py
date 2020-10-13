#!/usr/bin/python3
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
except ImportError as error:
    ## when import fails then it means that the script was executed indirectly
    ## in this case __init__ is already loaded
    pass

import sys

from PyQt5.QtWidgets import QApplication

from stockmonitor.gui.sigint import setup_interrupt_handling
from stockmonitor.gui.widget.stocktable import StockFullTable
from stockmonitor.dataaccess.gpw.gpwcurrentdata import GpwCurrentStockData

import teststockmonitor.data as data


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


app = QApplication(sys.argv)
app.setApplicationName("StockMonitor")
app.setOrganizationName("arnet")

# dataframe = DataFrame({'a': ['Mary', 'Jim', 'John'],
#                        'b': [100, 200, 300],
#                        'c': ['a', 'b', 'c']})

dataAccess = GpwCurrentStockData()
dataPath = data.get_data_path( "akcje_2020-04-14_15-50.xls" )
dataframe = dataAccess.parseDataFromFile( dataPath )

# csvPath = data.get_data_root_path() + "/akcje_2020-04-14_15-50.csv"
# dataframe.to_csv( csvPath, encoding='utf-8', index=False )

setup_interrupt_handling()

widget = StockFullTable()
widget.setColumnVisible( 0, False)
widget.setColumnVisible( 1, False)
widget.setColumnVisible( 3, False)
widget.setColumnVisible( 4, False)
widget.setColumnVisible(13, False)
widget.setColumnVisible(14, False)
widget.setColumnVisible(15, False)
widget.setColumnVisible(16, False)
widget.setColumnVisible(17, False)
widget.setColumnVisible(18, False)
widget.setColumnVisible(19, False)
widget.setColumnVisible(20, False)
widget.setColumnVisible(23, False)
# widget.tableSettings.setHeaderText(1, "changed header")
widget.resize( 1024, 768 )
widget.setData( dataframe )
widget.show()

widget.showColumnsConfiguration()

sys.exit( app.exec_() )
