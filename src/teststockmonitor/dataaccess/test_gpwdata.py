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

from teststockmonitor.data import get_data_path
from stockmonitor.dataaccess.gpwdata import GpwCurrentData, GpwIndexesData, GpwIndicatorsData, GpwIsinMapData
from stockmonitor.dataaccess.datatype import CurrentDataType


class GpwCurrentDataMock(GpwCurrentData):

    def getDataPath(self):
        return get_data_path( "akcje_2020-04-14_15-50.xls" )


## =================================================================


class GpwCurrentDataTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        self.dataAccess = GpwCurrentDataMock()
        self.dataAccess.parseDataFromDefaultFile()

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_getData(self):
        currData = self.dataAccess.getData( CurrentDataType.TICKER )
        dataLen = len( currData )
        self.assertEqual(dataLen, 391)      ## one removes, because if summary

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
#         self.dataAccess.getWorksheet( True )
#         end1Time = datetime.datetime.now()
#         self.dataAccess.loadWorksheet( False )
#         end2Time = datetime.datetime.now()
#         diff1 = end1Time - startTime
#         diff2 = end2Time - end1Time
#         print( "load time:", diff1, diff2 )


class GpwIndexesDataTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        self.dataAccess = GpwIndexesData()

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_getWorksheet(self):
        currData = self.dataAccess.getWorksheet()
        dataLen = len( currData )
        self.assertEqual(dataLen, 27)


class GpwIndicatorsDataTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        self.dataAccess = GpwIndicatorsData()

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_getWorksheet(self):
        currData = self.dataAccess.getWorksheet()
        dataLen = len( currData )
        self.assertEqual(dataLen, 437)


class GpwIsinMapDataTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        self.dataAccess = GpwIsinMapData()

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_getWorksheet(self):
        currData = self.dataAccess.getWorksheet()
        dataLen = len( currData )
        self.assertEqual(dataLen, 827)

#     def test_getWorksheet_micro(self):
#         startTime = datetime.datetime.now()
#         self.dataAccess.getWorksheet( True )
#         endTime = datetime.datetime.now()
#         diff = endTime - startTime
#         print( "load time:", diff )
