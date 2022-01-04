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
import abc

from typing import Dict

from stockmonitor.dataaccess.gpw.gpwintradaydata import GpwCurrentIndexIntradayData,\
    GpwCurrentStockIntradayData


_LOGGER = logging.getLogger(__name__)


class StockDataProvider():
    
#     @abc.abstractmethod
#     def refreshData(self, forceRefresh=True):
#         raise NotImplementedError('You need to define this method in derived class!')
    
    @abc.abstractmethod
    def accessData(self, forceRefresh=True):
        raise NotImplementedError('You need to define this method in derived class!')


## ==============================================================


class BaseWorksheetDAOProvider( StockDataProvider ):
    """Wrapper containing data custom headers."""

    def __init__( self, data: 'BaseWorksheetDAO' = None ):
        self.stockData: 'BaseWorksheetDAO'       = data
        self.stockHeaders: Dict[ int, str ]      = dict()

    @property
    def headers(self) -> Dict[ int, str ]:
        return self.stockHeaders

    ## override
    def accessData(self, forceRefresh=True):
        self.stockData.getWorksheetData( forceRefresh )


## ==================================================


class GpwStockIntradayMap( StockDataProvider ):

    def __init__(self):
        self.dataDict = dict()

    ## override
    def accessData(self, forceRefresh=True):
        for val in self.dataDict.values():
            val.getWorksheetData( forceRefresh )

    def getData(self, isin):
        source = self.getSource(isin)
        return source.getWorksheetData()

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

#     def getWorksheetData(self, forceRefresh=True):
#         for val in self.dataDict.values():
#             val.getWorksheetData( forceRefresh )


class GpwIndexIntradayMap( StockDataProvider ):

    def __init__(self):
        self.dataDict = dict()

    ## override
    def accessData(self, forceRefresh=True):
        for val in self.dataDict.values():
            val.getWorksheetData( forceRefresh )

    def getData(self, isin):
        source = self.getSource(isin)
        return source.getWorksheetData()

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

#     def getWorksheetData(self, forceRefresh=True):
#         for val in self.dataDict.values():
#             val.getWorksheetData( forceRefresh )
