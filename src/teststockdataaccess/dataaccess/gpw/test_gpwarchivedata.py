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
from stockdataaccess.dataaccess.datatype import StockDataType
from stockdataaccess.dataaccess.worksheetdata import WorksheetStorageMock
from stockdataaccess.dataaccess.gpw.gpwarchivedata import GpwArchiveData


## =================================================================


class GpwArchiveDataTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        day = datetime.date( 2022, 2, 10 )
        self.dataAccess = GpwArchiveData( day )

        def data_path():
            return get_data_path( "gpw_archive_2022-02-10_akcje.xls" )

        self.dataAccess.dao.getDataPath = data_path           # type: ignore
        self.dataAccess.dao.storage = WorksheetStorageMock()
        self.dataAccess.dao.parseWorksheetFromFile( data_path() )

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_getWorksheetData_False(self):
        currData = self.dataAccess.getWorksheetData( False )
        dataLen = len( currData )
        self.assertGreaterEqual(dataLen, 395)
        self.assertIsNotNone( currData )

#     def test_getWorksheet_micro(self):
#         startTime = datetime.datetime.now()
#         self.dataAccess.getWorksheetData( True )
#         end1Time = datetime.datetime.now()
#         self.dataAccess.loadWorksheet( False )
#         end2Time = datetime.datetime.now()
#         diff1 = end1Time - startTime
#         diff2 = end2Time - end1Time
#         print( "load time:", diff1, diff2 )

    def test_getStockData_None(self):
        currData = self.dataAccess.getStockData()
        self.assertEqual(currData, None)

    def test_getStockData(self):
        stockList = ["PL4FNMD00013", "LU2237380790"]
        currData = self.dataAccess.getStockData( stockList )
        dataLen = len( currData )
        self.assertEqual(dataLen, 2)

    def test_getData(self):
        currData = self.dataAccess.getData( StockDataType.ISIN )
        dataLen = len( currData )
        self.assertEqual(dataLen, 427)      ## one removed, because of summary

    def test_getRowByIsin(self):
        rowData = self.dataAccess.getRowByIsin( "LU2237380790" )
#         print( rowData )
        nameIndex = self.dataAccess.getDataColumnIndex( StockDataType.STOCK_NAME )
        isinIndex = self.dataAccess.getDataColumnIndex( StockDataType.ISIN )

        self.assertEqual( rowData[nameIndex], "ALLEGRO" )
        self.assertEqual( rowData[isinIndex], "LU2237380790" )

    def test_getIsinField(self):
        rowData = self.dataAccess.getIsinField( 4 )
        self.assertEqual( rowData, "PL4FNMD00013" )
