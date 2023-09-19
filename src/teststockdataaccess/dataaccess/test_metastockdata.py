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
        self.assertEqual(dataLen, 77389)

    def test_getWorksheetForDate(self):
        date_object = datetime.date( year=2020, month=9, day=21 )
        currData = self.dataAccess.getWorksheetForDate( date_object, True )
        dataLen = len( currData )
        self.assertEqual(dataLen, 77389)


class MetaStockIntradayDataCorruptTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        self.dataAccess = MetaStockIntradayData()

        def data_path():
            return get_data_path( "bossa-intraday-2023-03-15.prn" )

        self.dataAccess.dao.getDataPath = data_path                       # type: ignore
        self.dataAccess.dao.downloadData = lambda filePath: None          ## empty lambda function
        self.dataAccess.dao.storage = WorksheetStorageMock()

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_getWorksheetData_corrupt_row_ALIOR(self):
        ## raw data contains string in numeric field -- invalid rows should be filtered out

        currData = self.dataAccess.getWorksheetData( True )
        self.assertIsNotNone( currData )
        self.assertEqual( (3281, 10), currData.shape )

        stockData = currData[ currData["name"].eq( "ALIOR" ) ]

        priceColumn = stockData["kurs"]
        self.assertEqual( 36.94, priceColumn.iloc[-1] )

        minValue = priceColumn.min()
        maxValue = priceColumn.max()

        self.assertEqual( 36.9, minValue )
        self.assertEqual( 39.5, maxValue )

    def test_getWorksheetData_corrupt_row_BENEFIT(self):
        ## raw data contains string in numeric field -- invalid rows should be filtered out

        currData = self.dataAccess.getWorksheetData( True )
        self.assertIsNotNone( currData )
        self.assertEqual( (3281, 10), currData.shape )

        stockData = currData[ currData["name"].eq( "BENEFIT" ) ]

        priceColumn = stockData["kurs"]
        self.assertEqual( 1080.0, priceColumn.iloc[-1] )

        minValue = priceColumn.min()
        maxValue = priceColumn.max()

        self.assertEqual( 1080.0, minValue )
        self.assertEqual( 1095.0, maxValue )

    def test_getWorksheetData_corrupt_row_BIOCELTIX(self):
        ## raw data contains string in numeric field -- invalid rows should be filtered out

        currData = self.dataAccess.getWorksheetData( True )
        self.assertIsNotNone( currData )
        self.assertEqual( (3281, 10), currData.shape )

        stockData = currData[ currData["name"].eq( "BIOCELTIX" ) ]

        priceColumn = stockData["kurs"]
        self.assertEqual( 40.0, priceColumn.iloc[-1] )

        minValue = priceColumn.min()
        maxValue = priceColumn.max()

        self.assertEqual( 39.9, minValue )
        self.assertEqual( 40.0, maxValue )

    def test_getWorksheetData_corrupt_row_ORANGEPL(self):
        ## raw data contains string in numeric field -- invalid rows should be filtered out

        currData = self.dataAccess.getWorksheetData( True )
        self.assertIsNotNone( currData )
        self.assertEqual( (3281, 10), currData.shape )

        stockData = currData[ currData["name"].eq( "ORANGEPL" ) ]

        priceColumn = stockData["kurs"]
        self.assertEqual( 6.508, priceColumn.iloc[-1] )

        minValue = priceColumn.min()
        maxValue = priceColumn.max()

        self.assertEqual( 6.484, minValue )
        self.assertEqual( 6.524, maxValue )

    def test_getWorksheetData_valid(self):
        currData = self.dataAccess.getWorksheetData( True )
        self.assertIsNotNone( currData )
        self.assertEqual( (3281, 10), currData.shape )

        stockData = currData[ currData["name"].eq( "BNPPPL" ) ]

        priceColumn = stockData["kurs"]
        self.assertEqual( 46.8, priceColumn.iloc[-1] )

        minValue = priceColumn.min()
        maxValue = priceColumn.max()

        self.assertEqual( 46.0, minValue )
        self.assertEqual( 47.5, maxValue )
