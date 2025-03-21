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

from stockdataaccess.dataaccess.gpw.gpwintradaydata import GpwCurrentIndexIntradayData, \
    GpwCurrentStockIntradayData


_LOGGER = logging.getLogger(__name__)


class StockDataProvider():

#     @abc.abstractmethod
#     def refreshData(self, forceRefresh=True):
#         raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def getData(self, forceRefresh=True):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def accessData(self, forceRefresh=True):
        raise NotImplementedError('You need to define this method in derived class!')


## ==============================================================


class BaseWorksheetDAOProvider( StockDataProvider ):
    """Wrapper containing data custom headers."""

    def __init__( self, data=None ):
        self.stockData = data

    ## override
    def getData(self, forceRefresh=True):
        self.stockData.getWorksheetData( forceRefresh )

    ## override
    def accessData(self, forceRefresh=True):
        self.stockData.accessWorksheetData( forceRefresh )


class StockDataWrapper( BaseWorksheetDAOProvider ):
    """Wrapper containing data custom headers."""

    def __init__( self, data=None ):
        BaseWorksheetDAOProvider.__init__(self, data)
        self.stockHeaders: Dict[ int, str ]      = {}

    @property
    def headers(self) -> Dict[ int, str ]:
        return self.stockHeaders


## ==================================================


class DoubleDict():

    def __init__( self, factory_function=None ):
        self.dataDict = {}
        self.factory_function = factory_function

    def getData( self, key, subkey ):
        subDict = self._subdict( key )
        dictValue = subDict.get( subkey, None )
        if dictValue is None:
            dictValue = self.makeValue( key, subkey )
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
        for key, subDict in self.dataDict.items():
            for subkey in subDict:
                print( f"key: {key}-{subkey}" )

    def _subdict(self, key) -> dict:
        subDict = self.dataDict.get( key, None )
        if subDict is None:
            subDict = {}
            self.dataDict[ key ] = subDict
        return subDict

    def makeValue(self, key, subkey):
        if self.factory_function is None:
            return None
        return self.factory_function( key, subkey )


class WorksheetMap( StockDataProvider ):
    """Container for stock data for stock charts."""

    def __init__(self, factory_function=None):
        self.dataDict = DoubleDict( factory_function )

    def getSource(self, isin, rangeCode=None):
        if rangeCode is None:
            rangeCode = "1D"
        ret_data = self.dataDict.getData( isin, rangeCode )
        return ret_data

    ## override
    def getData(self, forceRefresh=True):
        values = self.dataDict.getValues()
        if len( values ) < 1:
            # _LOGGER.debug( "nothing to access (no open charts)" )
            return
        for val in values:
            val.getWorksheetData( forceRefresh )

    ## override
    def accessData(self, forceRefresh=True):
        values = self.dataDict.getValues()
        if len( values ) < 1:
            # _LOGGER.debug( "nothing to access (no open charts)" )
            return
        for val in values:
            val.accessWorksheetData( forceRefresh )

    def deleteData(self, isin):
        self.dataDict.deleteData(isin)

    def printData(self):
        self.dataDict.printData()


class GpwStockIntradayMap( WorksheetMap ):
    """Container for stock data for stock charts."""

    def __init__(self):
        super().__init__( GpwStockIntradayMap.makeValue )

    @staticmethod
    def makeValue(isin, rangeCode):
        return GpwCurrentStockIntradayData( isin, rangeCode )


class GpwIndexIntradayMap( WorksheetMap ):
    """Container for index data for index charts."""

    def __init__(self):
        super().__init__( GpwIndexIntradayMap.makeValue )

    @staticmethod
    def makeValue(isin, rangeCode):
        return GpwCurrentIndexIntradayData( isin, rangeCode )


# class GpwArchiveDataMap( WorksheetMap ):
#     """Container for stock data for stock charts."""
#
#     def __init__(self):
#         super().__init__( GpwArchiveDataMap.makeValue )
#
#     @staticmethod
#     def makeValue(isin, rangeCode):
#         return GpwArchiveData( isin, rangeCode )
