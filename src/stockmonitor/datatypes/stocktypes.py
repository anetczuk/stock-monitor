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

    ## override
    def accessData(self, forceRefresh=True):
        self.stockData.accessWorksheetData( forceRefresh )


class StockDataWrapper( BaseWorksheetDAOProvider ):
    """Wrapper containing data custom headers."""

    def __init__( self, data: 'BaseWorksheetDAO' = None ):
        BaseWorksheetDAOProvider.__init__(self, data)
        self.stockHeaders: Dict[ int, str ]      = dict()

    @property
    def headers(self) -> Dict[ int, str ]:
        return self.stockHeaders


## ==================================================


class RangeIntradayDict():
    
    def __init__(self):
        self.dataDict: Dict[ str, GpwCurrentStockIntradayData ] = dict()

    def getData(self, isin, rangeCode ) -> GpwCurrentStockIntradayData:
        source = self.dataDict.get( rangeCode, None )
        if source is not None:
            return source
        source = GpwCurrentStockIntradayData( isin, rangeCode )
        self.dataDict[ rangeCode ] = source
        return source
    
    def values(self):
        return self.dataDict.values()


class ISINIntradayDict():
    
    def __init__(self):
        self.dataDict: Dict[ str, RangeIntradayDict ] = dict()
        
    def getData(self, isin, rangeCode ) -> GpwCurrentStockIntradayData:
        rangeDict: RangeIntradayDict = self.dataDict.get( isin, None )
        if rangeDict is None:
            rangeDict = RangeIntradayDict()
            self.dataDict[ isin ] = rangeDict
        return rangeDict.getData( isin, rangeCode )
    
    def deleteData(self, isin):
        self.dataDict.pop( isin, None)
        
    def getValues(self):
        retList = []
        for rangeDict in self.dataDict.values():
            data = rangeDict.values()
            retList.extend( data )
        return retList
    
    def printData(self):
        for isin in self.dataDict:
            rangeDict: RangeIntradayDict = self.dataDict[ isin ]
            for rangeCode in rangeDict.dataDict:
                print( "key: %s-%s" % ( isin, rangeCode ) )


class GpwStockIntradayMap( StockDataProvider ):
    """Container for stock data for stock charts."""

    def __init__(self):
        self.dataDict: ISINIntradayDict = ISINIntradayDict()

    ## override
    def accessData(self, forceRefresh=True):
        values = self.dataDict.getValues()
        if len( values ) < 1:
            _LOGGER.debug( "nothing to access" )
            return
        for val in values:
            val.accessWorksheetData( forceRefresh )

#     def getData(self, isin) -> GpwCurrentStockIntradayData:
#         source: GpwCurrentStockIntradayData = self.getSource(isin)
#         return source.getWorksheetData()

    def deleteData(self, isin):
        self.dataDict.deleteData(isin)

    def getSource(self, isin, rangeCode=None) -> GpwCurrentStockIntradayData:
        if rangeCode is None:
            rangeCode = "1D"
        return self.dataDict.getData( isin, rangeCode )

    def printData(self):
        self.dataDict.printData()


class GpwIndexIntradayMap( StockDataProvider ):
    """Container for index data for index charts."""

    def __init__(self):
        self.dataDict = dict()

    ## override
    def accessData(self, forceRefresh=True):
        if len( self.dataDict ) < 1:
            _LOGGER.debug( "nothing to access" )
            return
        for val in self.dataDict.values():
            val.accessWorksheetData( forceRefresh )

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
