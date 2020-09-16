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

from stockmonitor.dataaccess.datatype import ArchiveDataType
from stockmonitor.dataaccess.gpw.gpwarchivedata import GpwArchiveData
from stockmonitor.dataaccess.gpw.gpwintradaydata import GpwCurrentStockIntradayData


_LOGGER = logging.getLogger(__name__)


class StockData(object):
    """Abstraction for stock data."""

    logger: logging.Logger = None

    def __init__(self):
        self.dataProvider = GpwArchiveData()

    def getData(self, dataType: ArchiveDataType, day: date):
        return self.dataProvider.getData( dataType, day )

    def getRecentValidDay(self, day: date ) -> datetime.date:
        return self.dataProvider.getRecentValidDay( day )

    def getNextValidDay(self, day: date):
        return self.dataProvider.getNextValidDay( day )

    def getISIN(self):
        day = date.today() - datetime.timedelta(days=1)
        return self.getISINForDate( day )

    def getISINForDate(self, day: date) -> dict:
        _LOGGER.info("loading recent ISIN data" )
        validDay = self.getRecentValidDay( day )
        return self.dataProvider.getData( ArchiveDataType.ISIN, validDay )

    def sourceLink(self):
        return self.dataProvider.sourceLink()


StockData.logger = _LOGGER.getChild(StockData.__name__)


class CounterDict:

    def __init__(self):
        self.counter = dict()

    def count(self, key):
        if key not in self.counter:
            self.counter[ key ] = 1
        else:
            self.counter[ key ] += 1


class StockDict:

    def __init__(self):
        self.stock = dict()

    def __getitem__(self, key):
        return self.stock[key]

    def __delitem__(self, key):
        del self.stock[key]

    def keys(self):
        return self.stock.keys()

    def addDict(self, dataDict):
        for key, value in dataDict:
            self.add( key, value )

    def add(self, key, value):
        if key in self.stock:
            self.stock[ key ] += value
            return
        self.stock[ key ] = value

    def max(self, data: dict):
        if data is None:
            return
        for key, val in data.items():
            if key not in self.stock:
                self.stock[ key ] = val
                continue
            if self.stock[ key ] < val:
                self.stock[ key ] = val

    def min(self, data: dict):
        if data is None:
            return
        for key, val in data.items():
            if key not in self.stock:
                self.stock[ key ] = val
                continue
            if self.stock[ key ] > val:
                self.stock[ key ] = val

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


## =========================================================================


class DataLoader():

    def __init__(self, day):
        self.day   = day
        self.func  = None

    def load(self, isinList, pool):
        self.func  = VarCalc.calcChange1
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