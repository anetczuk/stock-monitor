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

import logging

from typing import Dict

from stockmonitor.dataaccess.gpw.gpwintradaydata import GpwCurrentIndexIntradayData,\
    GpwCurrentStockIntradayData


_LOGGER = logging.getLogger(__name__)


class StockData():

    def __init__( self, data: object = None ):
        self.stockData                       = data
        self.stockHeaders: Dict[ int, str ]  = dict()

    @property
    def headers(self) -> Dict[ int, str ]:
        return self.stockHeaders

    def refreshData(self, forceRefresh=True):
        self.stockData.refreshData( forceRefresh )

    def loadWorksheet(self, forceRefresh=False):
        self.stockData.loadWorksheet( forceRefresh )

    def downloadData(self):
        self.stockData.downloadData()


class GpwStockIntradayMap():

    def __init__(self):
        self.dataDict = dict()

    def getData(self, isin):
        source = self.getSource(isin)
        return source.getWorksheet()

    def getSource(self, isin, rangeCode=None):
        if rangeCode is None:
            rangeCode = "1D"
        key = isin + "-" + rangeCode
        source = self.dataDict.get( key, None )
        if source is not None:
            return source
        source = GpwCurrentStockIntradayData( isin, rangeCode )
        self.dataDict[ key ] = source
        return source

    def set(self, isin, source):
        self.dataDict[ isin ] = source

    def refreshData(self, forceRefresh=True):
        for val in self.dataDict.values():
            val.refreshData( forceRefresh )


class GpwIndexIntradayMap():

    def __init__(self):
        self.dataDict = dict()

    def getData(self, isin):
        source = self.getSource(isin)
        return source.getWorksheet()

    def getSource(self, isin, rangeCode=None) -> GpwCurrentIndexIntradayData:
        if rangeCode is None:
            rangeCode = "1D"
        key = isin + "-" + rangeCode
        source = self.dataDict.get( key, None )
        if source is not None:
            return source
        source = GpwCurrentIndexIntradayData( isin, rangeCode )
        self.dataDict[ key ] = source
        return source

    def set(self, isin, source):
        self.dataDict[ isin ] = source

    def refreshData(self, forceRefresh=True):
        for val in self.dataDict.values():
            val.refreshData( forceRefresh )
