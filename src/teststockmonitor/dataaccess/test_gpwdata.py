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

from stockmonitor.dataaccess.gpwdata import GpwCurrentData, GpwCurrentCrawler
from stockmonitor.dataaccess.datatype import CurrentDataType

import os


script_dir = os.path.dirname(__file__)


class GpwCurrentCrawlerMock(GpwCurrentCrawler):
    def __init__(self):
        super().__init__()

    def getStockData(self):
        filePath = os.path.abspath( os.path.join(script_dir, "akcje_2020-04-14_15-50.xls") )
        return filePath

class GpwCurrentDataMock(GpwCurrentData):
    def __init__(self):
        super().__init__()
        self.crawler = GpwCurrentCrawlerMock()


## =================================================================


class GpwCurrentDataTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        self.dataAccess = GpwCurrentDataMock()

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_getData(self):
        currData = self.dataAccess.getData( CurrentDataType.SHORT )
        dataLen = len( currData )
        self.assertEqual(dataLen, 394)
