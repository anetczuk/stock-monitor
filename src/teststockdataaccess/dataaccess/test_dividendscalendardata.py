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

import unittest
import datetime
from teststockdataaccess.data import get_data_path

from stockdataaccess.dataaccess.dividendsdata import DividendsCalendarData
from stockdataaccess.dataaccess.worksheetdata import WorksheetStorageMock


class DividendsCalendarDataTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        self.dataAccess = DividendsCalendarData()

        def data_path():
            return get_data_path( "dividends_cal_data.html" )

        self.dataAccess.dao.getDataPath = data_path           # type: ignore
        self.dataAccess.dao.storage = WorksheetStorageMock()
        self.dataAccess.dao.parseWorksheetFromFile( data_path() )

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_getWorksheetData(self):
        currData = self.dataAccess.getWorksheetData()
        dataLen = len( currData )
        self.assertEqual( 2, dataLen )

    def test_getStockName(self):
        rowData = self.dataAccess.getStockName( 0 )
        self.assertEqual( "ALUMETAL", rowData )

    def test_getLawDate(self):
        rowData = self.dataAccess.getLawDate( 0 )
        self.assertEqual( datetime.date(2023, 4, 26), rowData )
