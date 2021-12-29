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
# import datetime

from teststockmonitor.data import get_data_path
from stockmonitor.dataaccess.datatype import CurrentDataType
from stockmonitor.dataaccess.gpw.gpwcurrentdata import GpwCurrentStockData,\
    GpwCurrentIndexesData
from stockmonitor.dataaccess.worksheetdata import WorksheetStorageMock


## =================================================================


class GpwCurrentStockDataTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        self.dataAccess = GpwCurrentStockData()

        def data_path():
            return get_data_path( "akcje_2021-12-21_20-00.xls" )

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

    def test_getData(self):
        currData = self.dataAccess.getData( CurrentDataType.TICKER )
        dataLen = len( currData )
        self.assertEqual(dataLen, 395)      ## one removes, because if summary

    def test_getStockData_None(self):
        currData = self.dataAccess.getStockData()
        self.assertEqual(currData, None)

    def test_getStockData(self):
        stockList = ["11B", "ALR"]
        currData = self.dataAccess.getStockData( stockList )
        dataLen = len( currData )
        self.assertEqual(dataLen, 2)

#     def test_getWorksheet_micro(self):
#         startTime = datetime.datetime.now()
#         self.dataAccess.getWorksheetData( True )
#         end1Time = datetime.datetime.now()
#         self.dataAccess.loadWorksheet( False )
#         end2Time = datetime.datetime.now()
#         diff1 = end1Time - startTime
#         diff2 = end2Time - end1Time
#         print( "load time:", diff1, diff2 )


# =================================================================


# class GpwCurrentIndexesDataTest(unittest.TestCase):
#
#     def setUp(self):
#         ## Called before testfunction is executed
#         self.dataAccess = GpwCurrentIndexesData()
#
#     def tearDown(self):
#         ## Called after testfunction was executed
#         pass
#
#     def test_getWorksheetData_False(self):
#         currData = self.dataAccess.getWorksheetData()
#         self.assertIsNone( currData )
#
#     def test_getWorksheetData_True(self):
#         currData = self.dataAccess.getWorksheetData( True )
#         dataLen = len( currData )
#         self.assertEqual(dataLen, 27)
