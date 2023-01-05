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

from stockdataaccess.dataaccess.metastockdata import MetaStockIntradayData
from stockdataaccess.dataaccess.worksheetdata import WorksheetStorageMock


class MetaStockIntradayDataTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        self.dataAccess = MetaStockIntradayData()

        def data_path():
            return get_data_path( "a_cgl_intraday_2020-08-17.prn" )

        self.dataAccess.dao.getDataPath = data_path                       # type: ignore
        self.dataAccess.dao.downloadData = lambda filePath: None          ## empty lambda function
        self.dataAccess.dao.storage = WorksheetStorageMock()

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_getWorksheetData_False(self):
        currData = self.dataAccess.getWorksheetData( False )
        self.assertIsNone( currData )

    def test_getWorksheetData_True(self):
        currData = self.dataAccess.getWorksheetData( True )
        dataLen = len( currData )
        self.assertEqual(dataLen, 77388)

    def test_getWorksheetForDate(self):
        date_object = datetime.date( year=2020, month=9, day=21 )
        currData = self.dataAccess.getWorksheetForDate( date_object, True )
        dataLen = len( currData )
        self.assertEqual(dataLen, 77388)