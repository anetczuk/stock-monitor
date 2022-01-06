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


class DoubleDict():

    def __init__( self, factory_function=None ):
        self.dataDict = dict()
        self.factory_function = factory_function

    def getData( self, key, subkey ):
        subDict = self._subdict( key )
        dictValue = subDict.get( subkey, None )
        if dictValue is None:
            dictValue = self._makeValue( key, subkey )
            subDict[ subkey ] = dictValue
        return dictValue

    def deleteData(self, key):
        self.dataDict.pop( key, None )
        
    def getValues(self):
        retList = []
        for subDict in self.dataDict.values():
            dictValue = subDict.values()
            retList.extend( dictValue )
        return retList
    
    def printData(self):
        for key in self.dataDict:
            subDict = self.dataDict[ key ]
            for subkey in subDict:
                print( "key: %s-%s" % ( key, subkey ) )
                
    def _subdict(self, key):
        subDict = self.dataDict.get( key, None )
        if subDict is None:
            subDict = dict()
            self.dataDict[ key ] = subDict
        return subDict
    
    def _makeValue(self, key, subkey):
        if self.factory_function is None:
            return None
        return self.factory_function( key, subkey )


class GpwStockIntradayMap( StockDataProvider ):
    """Container for stock data for stock charts."""

    def __init__(self):
        self.dataDict = DoubleDict( self._makeValue )

    ## override
    def accessData(self, forceRefresh=True):
        values = self.dataDict.getValues()
        if len( values ) < 1:
            _LOGGER.debug( "nothing to access" )
            return
        for val in values:
            val.accessWorksheetData( forceRefresh )

    def getSource(self, isin, rangeCode=None) -> GpwCurrentStockIntradayData:
        if rangeCode is None:
            rangeCode = "1D"
        return self.dataDict.getData( isin, rangeCode )

    def deleteData(self, isin):
        self.dataDict.deleteData(isin)

    def printData(self):
        self.dataDict.printData()
        
    def _makeValue(self, isin, rangeCode):
        return GpwCurrentStockIntradayData( isin, rangeCode )


class GpwIndexIntradayMap( StockDataProvider ):
    """Container for index data for index charts."""

    def __init__(self):
        self.dataDict = DoubleDict( self._makeValue )

    ## override
    def accessData(self, forceRefresh=True):
        values = self.dataDict.getValues()
        if len( values ) < 1:
            _LOGGER.debug( "nothing to access" )
            return
        for val in values:
            val.accessWorksheetData( forceRefresh )

    def getSource(self, isin, rangeCode=None) -> GpwCurrentIndexIntradayData:
        if rangeCode is None:
            rangeCode = "1D"
        return self.dataDict.getData( isin, rangeCode )

    def deleteData(self, isin):
        self.dataDict.deleteData(isin)

    def printData(self):
        self.dataDict.printData()

    def _makeValue(self, isin, rangeCode):
        return GpwCurrentIndexIntradayData( isin, rangeCode )
