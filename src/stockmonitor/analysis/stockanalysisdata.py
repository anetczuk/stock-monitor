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
import datetime
from datetime import date
import urllib
import math
import abc
import pandas

from stockdataaccess.dataaccess.datatype import StockDataType
from stockdataaccess.dataaccess.gpw.gpwarchivedata import GpwArchiveData
from stockdataaccess.dataaccess.gpw.gpwintradaydata import GpwCurrentStockIntradayData


_LOGGER = logging.getLogger(__name__)


class StockAnalysisData():
    """Abstraction for stock data."""

    def __init__(self):
        self.dataProvider: GpwArchiveData = GpwArchiveData()

    def getData(self, dataType: StockDataType, day: date):
        return self.dataProvider.getData( dataType, day )

    def getRecentValidDay(self, day: date ) -> datetime.date:
        return self.dataProvider.getRecentValidDay( day )

    def getNextValidDay(self, day: date):
        return self.dataProvider.getNextValidDay( day )

    def getISIN(self):
        day = date.today() - datetime.timedelta(days=1)
        return self.getISINForDate( day )

    ## returns Dict[ name, isin ]
    def getISINForDate(self, day: date) -> dict:
        validDay = self.getRecentValidDay( day )
        _LOGGER.info("loading recent ISIN data for %s", validDay )
        return self.dataProvider.getData( StockDataType.ISIN, validDay )

    def sourceLink(self):
        return self.dataProvider.sourceLink()


class CounterDict:

    def __init__(self):
        self.counter = {}

    def count(self, key):
        if key not in self.counter:
            self.counter[ key ] = 1
        else:
            self.counter[ key ] += 1


class StockDict:

    def __init__(self):
        self.stock = {}

    def __getitem__(self, key):
        return self.stock[key]

    def __setitem__(self, key, value):
        self.stock[key] = value

    def __delitem__(self, key):
        del self.stock[key]

    def keys(self):
        return self.stock.keys()

    def addDict(self, dataDict):
        for key, value in dataDict:
            self.add( key, value )

    def set(self, key, value):
        self.stock[ key ] = value

    def add(self, key, value):
        if key in self.stock:
            self.stock[ key ] += value
            return
        self.stock[ key ] = value

    def maxValue(self, key, value):
        if key in self.stock:
            maxVal = max( self.stock[ key ], value )
            self.stock[ key ] = maxVal
            return
        self.stock[ key ] = value

    def max(self, data: dict):
        if data is None:
            return
        for key, val in data.items():
            self.maxValue( key, val )

    def minValue(self, key, value):
        if key in self.stock:
            self.stock[ key ] = min( self.stock[ key ], value )
            return
        self.stock[ key ] = value

    def min(self, data: dict):
        if data is None:
            return
        for key, val in data.items():
            self.minValue( key, val )

    def sum(self, data: dict, factor=1.0):
        if data is None:
            return
        for key, val in data.items():
            if key not in self.stock:
                self.stock[ key ] = val * factor
                continue
            self.stock[ key ] = self.stock[ key ] + val * factor

    def div(self, data: dict):
        if data is None:
            return
        for key, val in self.stock.items():
            if key not in data:
                continue
            self.stock[ key ] = val / data[ key ]

    def abs(self):
        for key, val in self.stock.items():
            if val < 0.0:
                self.stock[ key ] = abs( val )

    # |val - avg|/avg
    @staticmethod
    def var(valDict, avgDict):
        diffDict = StockDict()
        diffDict.sum( valDict )
        diffDict.sum( avgDict, -1.0 )
        diffDict.abs()
        diffDict.div( avgDict )
        return diffDict


class StockDictList():

    def __init__(self):
        self.dataDict = {}

    def __getitem__(self, key):
        return self.get( key )

    def subkeys(self):
        retList = set()
        for subdict in self.dataDict.values():
            subkeys = subdict.keys()
            retList |= subkeys
        return retList

    def get(self, key):
        data = self.dataDict.get( key, None )
        if data is None:
            self.dataDict[ key ] = StockDict()
        return self.dataDict[ key ]

    def generateDataFrame( self, namesSet ):
        keysList = self.dataDict.keys()
        columnsList = ["name"] + list( keysList )
        rowsList = []
        for name in namesSet:
            dataRow = [ name ]
            for column in keysList:
                value = self.dataDict[ column ][ name ]
                dataRow.append( value )
            rowsList.append( dataRow )
        retDataFrame = pandas.DataFrame.from_records( rowsList, columns=columnsList )
        return retDataFrame


class StatsDict():

    class SubDict():
        """Sub dictionary."""

        def __init__(self):
            self.valueDict = {}

        def __getitem__(self, key):
            return self.valueDict[ key ]

        def __setitem__(self, key, value):
            self.valueDict[ key ] = value

        def keys(self):
            return self.valueDict.keys()

        def values(self):
            return self.valueDict.values()

        def get(self, field, defaultValue=None):
            currVal = self.valueDict.get(field)
            if currVal is None:
                return defaultValue
            return currVal

        def minValue(self, key, value):
            currVal = self.valueDict.get(key)
            if currVal is None:
                self.valueDict[ key ] = value
            else:
                if currVal > value:
                    self.valueDict[ key ] = value

        def maxValue(self, key, value):
            currVal = self.valueDict.get(key)
            if currVal is None:
                self.valueDict[ key ] = value
            else:
                if currVal < value:
                    self.valueDict[ key ] = value

        def add(self, field, value):
            currVal = self.valueDict.get( field )
            if currVal is None:
                self.valueDict[ field ] = value
            else:
                self.valueDict[ field ] = currVal + value

        def addElems(self, fieldsDict: 'StatsDict.SubDict'):
            fieldsSet = fieldsDict.keys()
            for field in fieldsSet:
                value = fieldsDict[ field ]
                self.add( field, value )

        def div(self, field, value):
            currVal = self.valueDict.get(field)
            if currVal is None:
                self.valueDict[ field ] = 0
            else:
                self.valueDict[ field ] = currVal / value

        def divFields(self, value):
            fieldsSet = self.valueDict.keys()
            for field in fieldsSet:
                self.div( field, value )

        ## pprint
        def printData(self, indent=0):
            StatsDict.pprint( self.valueDict, indent )

    ## =====================================================================

    def __init__(self):
        self.dataDict = {}      ## ticker => fields dict

    def __getitem__(self, key):
        data = self.dataDict.get( key, None )
        if data is None:
            self.dataDict[ key ] = StatsDict.SubDict()
        return self.dataDict[ key ]
#         return self.get( key )

    def empty(self):
        return not self.dataDict

    def keys(self):
        return self.dataDict.keys()

#     def subkeys(self):
#         retList = set()
#         for subdict in self.dataDict.values():
#             subkeys = subdict.keys()
#             retList |= subkeys
#         return retList

#     def get(self, key):
#         data = self.dataDict.get( key, None )
#         if data is None:
#             self.dataDict[ key ] = StockDict()
#         return self.dataDict[ key ]

    def addValue(self, field, value):
        for fieldsDict in self.dataDict.values():
            fieldsDict.add( field, value )

    def add(self, field, dataDict: 'StatsDict'):
        namesSet = dataDict.keys()
        for name in namesSet:
            fieldsDict = dataDict[ name ]
            fieldValue = fieldsDict.get( field, 0 )
            currFields = self[ name ]
            currFields.add( field, fieldValue )

    def rem(self, field, dataDict: 'StatsDict'):
#         for fieldsDict in self.dataDict.values():
#             fieldsDict.divFields( value )
        namesSet = dataDict.keys()
        for name in namesSet:
            fieldsDict = dataDict[ name ]
            fieldValue = fieldsDict.get( field, 0 )
            currFields = self[ name ]
            currFields.add( field, -fieldValue )

    def addElems(self, dataDict: 'StatsDict'):
        namesSet = dataDict.keys()
        for name in namesSet:
            fieldsDict = dataDict[ name ]
            currFields = self[ name ]
            currFields.addElems( fieldsDict )

    def divFields(self, value):
        for fieldsDict in self.dataDict.values():
            fieldsDict.divFields( value )

    def generateDataFrame( self, namesSet ):
        nameValues = self.dataDict.values()
        if not nameValues:
            # empty
            return pandas.DataFrame()
        firstValue = list(nameValues)[0]
        keysList = firstValue.keys()
#         keysList = self.dataDict.keys()
        columnsList = ["name"] + list( keysList )
        rowsList = []
        for name in namesSet:
            dataRow = [ name ]
            nameValues = self.dataDict[ name ]
#             for column in keysList:
#                 value = nameValues[ column ]
#                 dataRow.append( value )
#             rowsList.append( dataRow )
            values = list( nameValues.values() )
            rowsList.append( dataRow + values )
        retDataFrame = pandas.DataFrame.from_records( rowsList, columns=columnsList )
        return retDataFrame

    ## pprint
    def printData(self, indent=0):
        StatsDict.pprint( self.dataDict, indent )

    @staticmethod
    def pprint(d, indent=0):
        if d is None:
            print('\t' * indent + "None")
            return
        if not d:
            ## empty container
            print('\t' * indent + "Empty")
            return

        for key, value in d.items():
            print('\t' * indent + str(key))
            if isinstance( value, dict ):
                StatsDict.pprint( value, indent + 1 )
            elif isinstance( value, StatsDict.SubDict ):
                StatsDict.pprint( value.valueDict, indent + 1 )
            else:
                print('\t' * (indent + 1) + str(value))


## =========================================================================


class DataProcessor():
    """Threaded data processor."""

    def __init__( self, attempts=3 ):
        self.attempts = attempts

    @abc.abstractmethod
    def processData(self, params):
        raise NotImplementedError('You need to define this method in derived class!')

    ## returns list
    def map(self, paramsList, pool):
        return pool.map( self._calc, paramsList )

    def _calc(self, params):
        for _ in range(0, self.attempts):
            try:
                return self.processData( params )
#             except urllib.error.HTTPError as e:
#                 _LOGGER.info( "exception: %s", str(e) )
            except urllib.error.URLError as e:
                _LOGGER.info( "exception: %s", str(e) )
        return self.processData( params )


class SourceDataLoader( DataProcessor ):
    """Threaded data loader."""

    def __init__(self, source):
        super().__init__()
        self.source = source

    def processData(self, params):
        return self.source.load( params )


class GpwCurrentIntradayDataLoader( DataProcessor ):
    """Threaded data loader."""

    def __init__(self, day):
        super().__init__()
        self.day = day

    def processData(self, params):
        name, isin   = params
        intradayData = GpwCurrentStockIntradayData( isin )
        dataFrame    = intradayData.getWorksheetForDate( self.day )
        return (name, dataFrame)


class VarCalc():

    def __init__(self, day):
        self.day   = day
        self.func  = None
        self.cName = None

    def load(self, isinList, pool):
        self.func  = VarCalc.calcChange1
        return pool.map( self._calc, isinList )

    def calculateChange1(self, colName, isinList, pool):
        self.func  = VarCalc.calcChange1
        self.cName = colName
        return pool.map( self._calc, isinList )

    def calculateChange2(self, colName, isinList, pool):
        self.func  = VarCalc.calcChange2
        self.cName = colName
        return pool.map( self._calc, isinList )

    def calculateStdDev(self, colName, isinList, pool):
        self.func  = VarCalc.calcStdDev
        self.cName = colName
        return pool.map( self._calc, isinList )

    def calculateVar(self, colName, isinList, pool):
        self.func  = VarCalc.calcVar
        self.cName = colName
        return pool.map( self._calc, isinList )

    def calculateSum(self, colName, isinList, pool):
        self.func  = VarCalc.calcSum
        self.cName = colName
        return pool.map( self._calc, isinList )

    def _calc(self, isin):
        for _ in range(0, 3):
            try:
                return self._calcSingle( isin )
            except urllib.error.URLError as e:
                _LOGGER.info( "exception: %s", str(e) )
        return self._calcSingle( isin )

    def _calcSingle(self, key):
        name, isin = key
        intradayData = GpwCurrentStockIntradayData( isin )
        dataFrame    = intradayData.getWorksheetForDate( self.day )
        if dataFrame is None:
            ## no data
            return (name, 0)

        dataColumn = dataFrame[ self.cName ]
        value = self.func( dataColumn )
        if math.isnan(value):
            return (name, 0)
        return (name, value)

    @staticmethod
    def calcActivity(dataColumn):
        if dataColumn.count() < 2:
            return 0.0
        refval = dataColumn.mean()
        diff = dataColumn.diff().abs()
        val = abs( diff.sum() / refval * 100 )
        return val

    @staticmethod
    def calcChange1(dataColumn):
        if dataColumn.count() < 2:
            return 0.0
        refval = dataColumn.min()
        normColumn = dataColumn.div( refval ) * 100
#         diff = normColumn.diff().abs()
        diff = normColumn.diff()
        return diff.sum()

    @staticmethod
    def calcChange2(dataColumn):
        if dataColumn.count() < 2:
            return 0.0
        pmin = dataColumn.min()
#         pmax = dataColumn.max()
#         pdiff = pmax - pmin
        pdiff = dataColumn.median() - pmin
        pthresh = pmin + pdiff * 0.3
        pcount = dataColumn[dataColumn > pthresh].count()
#         priceVar     = dataColumn.quantile( 0.1 )
        return pcount

    ## return list of pairs: List[ ( change sum, num of changes ) ]
    @staticmethod
    def calcChange3(dataColumn, minPercent):
        if dataColumn.count() < 2:
            return (0.0, 0)
        minDiff = minPercent / 100.0

        dataSize = len( dataColumn )
        dataList = []
        dataList.append( dataColumn[0] )
        dataList.append( dataColumn[1] )
        for i in range(2, dataSize):
            recentDiff = dataList[-1] - dataList[-2]
            currDiff   = dataColumn[i] - dataColumn[i - 1]
            if recentDiff > 0:
                if currDiff > 0:
                    dataList[-1] += currDiff
                    continue
            else:
                if currDiff < 0:
                    dataList[-1] += currDiff
                    continue
            dataList.append( dataColumn[i] )

        diff    = 0.0
        counter = 0
        dataSize = len( dataList )
        localMin = dataList[0]
        localMax = dataList[0]
        for i in range(1, dataSize):
            minRaise = (dataList[i] - localMin) / localMin
            maxRaise = (dataList[i] - localMax) / localMax
            currRaise = max( minRaise, maxRaise )
            if currRaise > minDiff:
                diff += currRaise
                counter += 1
                localMin = dataList[i]
                localMax = dataList[i]
                continue
            if minRaise < 0:
                localMin = dataList[i]
            if maxRaise > 0:
                localMax = dataList[i]

#             minRaise = (dataList[i] - localMin) / localMin
#             maxRaise = (dataList[i] - localMax) / localMax
#             currDiff = max( abs(minRaise), abs(maxRaise) )
#             if currDiff > minDiff:
#                 diff += currDiff
#                 counter += 1
#                 localMin = dataList[i]
#                 localMax = dataList[i]
#                 continue
#             if minRaise < 0:
#                 localMin = dataList[i]
#             if maxRaise > 0:
#                 localMax = dataList[i]

        return (diff * 100, counter)

    @staticmethod
    def calcStdDev(dataColumn):
        if dataColumn.count() < 2:
            return 0.0
        diff = dataColumn.diff()
        diff = diff.fillna(0.0)
        return diff.std()

    @staticmethod
    def calcVar(dataColumn):
        if dataColumn.count() < 2:
            return 0.0
        diff = dataColumn.diff()
        return diff.var()

    @staticmethod
    def calcSum(dataColumn):
        if dataColumn.count() < 1:
            return 0.0
        return dataColumn.sum()
