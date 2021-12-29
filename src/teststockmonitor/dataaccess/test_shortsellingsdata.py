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
from teststockmonitor.data import get_data_path

from stockmonitor.dataaccess.shortsellingsdata import CurrentShortSellingsData, HistoryShortSellingsData
from stockmonitor.dataaccess.worksheetdata import WorksheetStorageMock


class CurrentShortSellingsDataTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        self.dataAccess = CurrentShortSellingsData()

        def data_path():
            return get_data_path( "shortsellings-current.html" )
  
        self.dataAccess.dao.getDataPath = data_path           # type: ignore
        self.dataAccess.dao.storage = WorksheetStorageMock()
        self.dataAccess.dao.parseWorksheetFromFile( data_path() )

    def tearDown(self):
        ## Called after testfunction was executed
        pass

#     def test__grabContent(self):
#         url = self.dataAccess.getDataUrl()
#         content = self.dataAccess._grabContent( url )
#         self.assertTrue( content )
#         print( "grabbed content:\n", content )

    def test_getWorksheetData(self):
        currData = self.dataAccess.getWorksheetData( False )
        dataLen = len( currData )
        self.assertEqual(dataLen, 5)
 
    def test_getISIN(self):
#         print( self.dataAccess.getWorksheetData() )
        rowData = self.dataAccess.getISIN( 3 )
        self.assertEqual( rowData, "PLOPTTC00011" )


class HistoryShortSellingsDataTest(unittest.TestCase):
 
    def setUp(self):
        ## Called before testfunction is executed
        self.dataAccess = HistoryShortSellingsData()
 
        def data_path():
            return get_data_path( "shortsellings-history.html" )
 
        self.dataAccess.dao.getDataPath = data_path           # type: ignore
        self.dataAccess.dao.storage = WorksheetStorageMock()
        self.dataAccess.dao.parseWorksheetFromFile( data_path() )
 
    def tearDown(self):
        ## Called after testfunction was executed
        pass
 
    def test_getWorksheetData(self):
        currData = self.dataAccess.getWorksheetData( False )
        dataLen = len( currData )
        self.assertEqual(dataLen, 30)
        
    def test_getISIN(self):
#         print( self.dataAccess.getWorksheetData() )
        rowData = self.dataAccess.getISIN( 3 )
        self.assertEqual( rowData, "PL11BTS00015" )
