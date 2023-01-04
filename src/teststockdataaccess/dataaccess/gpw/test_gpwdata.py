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

from teststockdataaccess.data import get_data_path
from stockdataaccess.dataaccess.gpw.gpwdata import GpwIndicatorsData, GpwIsinMapData
from stockdataaccess.dataaccess.worksheetdata import WorksheetStorageMock


class GpwIndicatorsDataTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        self.dataAccess = GpwIndicatorsData()

        def data_path():
            return get_data_path( "indicators_data.html" )

        self.dataAccess.dao.getDataPath = data_path                 # type: ignore
        self.dataAccess.dao.storage = WorksheetStorageMock()
        self.dataAccess.dao.parseWorksheetFromFile( data_path() )       ## load raw data

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_getWorksheetData_False(self):
        currData = self.dataAccess.getWorksheetData( False )
        dataLen = len( currData )
        self.assertGreaterEqual(dataLen, 400)
        self.assertIsNotNone( currData )

    def test_getStockIsin(self):
        rowData = self.dataAccess.getStockIsin( 3 )
        self.assertEqual( rowData, "PLGRNKT00019" )


class GpwIsinMapDataTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        self.dataAccess = GpwIsinMapData()

        def data_path():
            return get_data_path( "isin_map_data.html" )

        self.dataAccess.dao.getDataPath = data_path           # type: ignore
        self.dataAccess.dao.storage = WorksheetStorageMock()
        self.dataAccess.dao.parseWorksheetFromFile( data_path() )

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_getWorksheetData(self):
        currData = self.dataAccess.getWorksheetData()
        dataLen = len( currData )
        self.assertEqual(dataLen, 829)

#     def test_getWorksheet_micro(self):
#         startTime = datetime.datetime.now()
#         self.dataAccess.getWorksheetData( True )
#         endTime = datetime.datetime.now()
#         diff = endTime - startTime
#         print( "load time:", diff )

    def test_getTickerFromIsin(self):
#         print( self.dataAccess.getWorksheetData() )
        rowData = self.dataAccess.getTickerFromIsin( "PL4FNMD00013" )
        self.assertEqual( rowData, "4FM" )

    def test_getTickerFromName(self):
#         print( self.dataAccess.getWorksheetData() )
        rowData = self.dataAccess.getTickerFromName( "4FUNMEDIA" )
        self.assertEqual( rowData, "4FM" )

    def test_getStockIsinFromTicker(self):
#         print( self.dataAccess.getWorksheetData() )
        rowData = self.dataAccess.getStockIsinFromTicker( "4FM" )
        self.assertEqual( rowData, "PL4FNMD00013" )

    def test_getNameFromTicker(self):
#         print( self.dataAccess.getWorksheetData() )
        rowData = self.dataAccess.getNameFromTicker( "4FM" )
        self.assertEqual( rowData, "4Fun Media SA" )
