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

import os
import logging
import datetime
from datetime import date
import calendar
import urllib
import math
import multiprocessing.dummy

from typing import Dict, List

import csv
import pandas

from stockmonitor.dataaccess import tmp_dir
from stockmonitor.dataaccess.datatype import ArchiveDataType
from stockmonitor.dataaccess.gpwdata import GpwArchiveData,\
    GpwCurrentStockIntradayData


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


## =========================================================================


class StockAnalysis(object):
    """Analysis of stock data."""

    logger: logging.Logger = None

    def __init__(self):
        self.data = StockData()
        self.isinDict = None

        self.minValue  = None
        self.minDate   = None
        self.maxValue  = None
        self.maxDate   = None
        self.sumValue  = None
        self.sumDate   = None
        self.currValue = None
        self.currDate  = None

    def sourceLink(self):
        return self.data.sourceLink()

    def loadMin(self, dataType: ArchiveDataType, fromDay: date, toDay: date):
        nowDate = datetime.datetime.now().date()
        if fromDay >= nowDate:
            fromDay = nowDate - datetime.timedelta(days=1)
        if toDay >= nowDate:
            toDay = nowDate - datetime.timedelta(days=1)
        self.logger.debug( "Loading min in range: %s %s", fromDay, toDay )
        currDate = fromDay
        ret = StockDict()
        while currDate <= toDay:
            dayValues = self.data.getData( dataType, currDate )
            ret.min( dayValues )
            currDate += datetime.timedelta(days=1)
        self.minValue = ret.stock
        self.minDate  = [fromDay, toDay]

    def loadMax(self, dataType: ArchiveDataType, fromDay: date, toDay: date):
        nowDate = datetime.datetime.now().date()
        if fromDay >= nowDate:
            fromDay = nowDate - datetime.timedelta(days=1)
        if toDay >= nowDate:
            toDay = nowDate - datetime.timedelta(days=1)
        self.logger.debug( "Loading max in range: %s %s", fromDay, toDay )
        currDate = fromDay
        ret = StockDict()
        while currDate <= toDay:
            dayValues = self.data.getData( dataType, currDate )
            ret.max( dayValues )
            currDate += datetime.timedelta(days=1)
        self.maxValue = ret.stock
        self.maxDate  = [fromDay, toDay]

    def loadSum(self, dataType: ArchiveDataType, fromDay: date, toDay: date):
        nowDate = datetime.datetime.now().date()
        if fromDay >= nowDate:
            fromDay = nowDate - datetime.timedelta(days=1)
        if toDay >= nowDate:
            toDay = nowDate - datetime.timedelta(days=1)
        self.logger.debug( "Loading sum in range: %s %s", fromDay, toDay )
        currDate = fromDay
        ret = StockDict()
        while currDate <= toDay:
            _LOGGER.debug( "accessing data for dat: %s", currDate )
            dayValues = self.data.getData( dataType, currDate )
            ret.sum( dayValues )
            currDate += datetime.timedelta(days=1)
        self.sumValue = ret.stock
        self.sumDate  = [fromDay, toDay]

    def loadCurr(self, dataType: ArchiveDataType, day: date=date.today(), offset=-1):
        _LOGGER.debug( "Loading current: %s %s %s", dataType, day, offset )
        currDay  = day + datetime.timedelta(days=offset)
        nowDate = datetime.datetime.now().date()
        if currDay >= nowDate:
            currDay = nowDate - datetime.timedelta(days=1)
        validDay = self.data.getRecentValidDay( currDay )
        _LOGGER.debug( "valid day: %s", validDay )
        self.currValue = self.data.getData( dataType, validDay )
        self.currDate  = [validDay]

    def loadData(self, dataType: ArchiveDataType, day: date):
        return self.data.getData( dataType, day )

    def calcGreatestSum(self, outFilePath=None):
        file = outFilePath
        if file is None:
            file = tmp_dir + "out/output_sum.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )

        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["reference period:", dates_to_string(self.sumDate) ] )
        writer.writerow( [] )

        columnsList = ["name", "val sum", "trading[k]", "link"]

        rowsList = []

        currTrading = self.loadData( ArchiveDataType.TRADING, self.currDate[0] )

        for key, val in self.sumValue.items():
            tradingVal = currTrading[ key ]
            moneyLink = self.getMoneyPlLink( key )
            rowsList.append( [key, val, tradingVal, moneyLink] )

        ## sort by trading
        rowsList.sort(key=lambda x: x[1], reverse=True)

        writer.writerow( columnsList )
        for row in rowsList:
            writer.writerow( row )

        retDataFrame = pandas.DataFrame.from_records( rowsList, columns=columnsList )

        self.logger.debug( "Done" )

        return retDataFrame

    def calcGreater(self, level, outFilePath=None):
        file = outFilePath
        if file is None:
            file = tmp_dir + "out/output_raise.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )

        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["reference period:", dates_to_string(self.currDate) ] )
        writer.writerow( ["reference level:", level ] )
        writer.writerow( ["formula:", "reference > level"] )
        writer.writerow( [] )

        writer.writerow( ["name", "curr val", "link"] )

        rowsList = []

        for key, val in self.currValue.items():
            if val > level:
                moneyLink = self.getMoneyPlLink( key )
                rowsList.append( [key, val, moneyLink] )

        ## sort by potential
        rowsList.sort(key=lambda x: x[1], reverse=True)

        for row in rowsList:
            writer.writerow( row )

        self.logger.debug( "Found companies: %s", len(rowsList) )

    def calcPotentials(self, outFilePath=None):
        self.logger.info( "Calculating potential" )

        if outFilePath is None:
            outFilePath = tmp_dir + "out/output_potentials.csv"
        dirPath = os.path.dirname( outFilePath )
        os.makedirs( dirPath, exist_ok=True )

        writer = csv.writer(open(outFilePath, 'w'))
        writer.writerow( ["min period:", dates_to_string(self.minDate) ] )
        writer.writerow( ["max period:", dates_to_string(self.maxDate) ] )
        writer.writerow( ["recent val date:", dates_to_string(self.currDate) ] )
        writer.writerow( ["potential:", "(max - curr) / max"] )
        writer.writerow( ["relative:",  "(max - curr) / (max - min)"] )
        writer.writerow( [] )

        columnsList = ["name", "min val", "max val", "curr val", "trading[k]", "potential", "relative", "link"]
        rowsList = []

        currTrading = self.loadData( ArchiveDataType.TRADING, self.currDate[0] )

        for key, currVal in self.currValue.items():
            maxVal = self.maxValue.get( key )
            if maxVal is None or maxVal == 0:
                ## new stock, ignore
                continue
            minVal = self.minValue[ key ]
            tradingVal = currTrading[ key ]
            raiseVal = maxVal - currVal
            potVal = raiseVal / maxVal
            stockDiff = maxVal - minVal
            relVal = 0
            if stockDiff != 0:
                relVal = raiseVal / stockDiff
            moneyLink = self.getMoneyPlLink( key )
            potVal = round( potVal, 4 )
            relVal = round( relVal, 4 )
            rowsList.append( [key, minVal, maxVal, currVal, tradingVal, potVal, relVal, moneyLink] )

        writer.writerow( columnsList )
        for row in rowsList:
            writer.writerow( row )

        retDataFrame = pandas.DataFrame.from_records( rowsList, columns=columnsList )

        self.logger.debug( "Done" )

        return retDataFrame

    # pylint: disable=R0914
    def calcBestRaise(self, level, outFilePath=None):
        self.logger.info( "Calculating best raise for level: %s", level )

        file = outFilePath
        if file is None:
            file = tmp_dir + "out/output_raise.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )

        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["max period:", dates_to_string(self.maxDate) ] )
        writer.writerow( ["min period:", dates_to_string(self.minDate) ] )
        writer.writerow( ["reference period:", dates_to_string(self.currDate) ] )
        writer.writerow( ["reference level:", level ] )
        writer.writerow( ["formula:", "(reference - min) < (max - min) * level"] )
        writer.writerow( [] )

        writer.writerow( ["name", "max val", "min val", "curr val", "trading[k]", "potential", "link"] )

        rowsList = []

        currTrading = self.loadData( ArchiveDataType.TRADING, self.currDate[0] )

        for key, currVal in self.currValue.items():
            maxVal = self.maxValue.get( key )
            if maxVal is None:
                ## new stock, ignore
                continue
            minVal = self.minValue[ key ]
            stockDiff = maxVal - minVal
            currDiff = currVal - minVal
            refDiff = stockDiff * level
            if currDiff < refDiff:
                raiseVal = maxVal - currVal
                pot = 0
                if currVal != 0:
                    pot = raiseVal / currVal
                tradingVal = currTrading[ key ]
                moneyLink = self.getMoneyPlLink( key )
                rowsList.append( [key, maxVal, minVal, currVal, tradingVal, pot, moneyLink] )

        ## sort by potential
        rowsList.sort(key=lambda x: x[5], reverse=True)

        for row in rowsList:
            writer.writerow( row )

        self.logger.debug( "Found companies: %s", len(rowsList) )

    def calcBestValue(self, level, outFilePath=None):
        self.logger.info( "Calculating best value for level: %s", level )

        file = outFilePath
        if file is None:
            file = tmp_dir + "out/output_value.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )

        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["max period:", dates_to_string(self.maxDate) ] )
        writer.writerow( ["reference period:", dates_to_string(self.currDate) ] )
        writer.writerow( ["reference level:", level ] )
        writer.writerow( ["formula:", "reference < max * level"] )
        writer.writerow( [] )

        writer.writerow( ["name", "max val", "curr val", "trading[k]", "potential", "link"] )

        rowsList = []

        currTrading = self.loadData( ArchiveDataType.TRADING, self.currDate[0] )

        for key, currVal in self.currValue.items():
            maxVal = self.maxValue.get( key )
            if maxVal is None:
                ## new stock, ignore
                continue
            refLevel = maxVal * level
            if currVal < refLevel:
                pot = ""
                if currVal != 0:
                    pot = maxVal / currVal
                tradingVal = currTrading[ key ]
                moneyLink = self.getMoneyPlLink( key )
                rowsList.append( [key, maxVal, currVal, tradingVal, pot, moneyLink] )

        ## sort by potential
        rowsList.sort(key=lambda x: x[4], reverse=True)

        for row in rowsList:
            writer.writerow( row )

        self.logger.debug( "Found companies: %s", len(rowsList) )

    def calcBiggestRaise(self, level, outFilePath=None):
        file = outFilePath
        if file is None:
            file = tmp_dir + "out/output_raise.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )

        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["max period:", dates_to_string(self.maxDate) ] )
        writer.writerow( ["reference period:", dates_to_string(self.currDate) ] )
        writer.writerow( ["reference level:", level ] )
        writer.writerow( ["formula:", "reference > max * level"] )
        writer.writerow( [] )

        writer.writerow( ["name", "max val", "curr val", "potential", "link"] )

        rowsList = []

        for key, val in self.currValue.items():
            maxVal = self.maxValue[ key ]
            refLevel = maxVal * level
            if val > refLevel:
                pot = 0
                if maxVal > 0:
                    pot = val / maxVal
                moneyLink = self.getMoneyPlLink( key )
                rowsList.append( [key, maxVal, val, pot, moneyLink] )

        ## sort by potential
        rowsList.sort(key=lambda x: x[3], reverse=True)

        for row in rowsList:
            writer.writerow( row )

        self.logger.debug( "Found companies: %s", len(rowsList) )

    def calcMonday(self, numOfWeeks=1, lastDay: date=date.today(), outFilePath=None):
        self.logger.info( "Calculating Monday stock" )
        return self._calcDayOfWeek( 0, numOfWeeks, lastDay, outFilePath, True )

    def calcFriday(self, numOfWeeks=1, lastDay: date=date.today(), outFilePath=None):
        self.logger.info( "Calculating Friday stock" )
        return self._calcDayOfWeek( 4, numOfWeeks, lastDay, outFilePath, False )

    # pylint: disable=R0914
    def calcWeekend(self, numOfWeeks=1, lastDay: date=date.today(), outFilePath=None):
        file = outFilePath
        if file is None:
            file = tmp_dir + "out/weekend_change.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )

        lastValid = self.getRecentValidDay( lastDay )
        weekDay = lastValid.weekday()                               # 0 for Monday
        lastMonday = lastValid - datetime.timedelta(days=weekDay)

        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["last monday:", str(lastMonday) ] )
        writer.writerow( ["num of weeks:", numOfWeeks ] )
        writer.writerow( [] )

        columnsList = ["name", "friday val", "monday val", "potential", "accuracy", "link"]

        raiseCounter = CounterDict()
        counterMonday = lastMonday

        for _ in range(0, numOfWeeks):
            prevDay = self.getRecentValidDay(counterMonday)
            nextDay = self.getNextValidDay(counterMonday)

            ## calc
            prevValue = self.data.getData( ArchiveDataType.CLOSING, prevDay )
            nextValue = self.data.getData( ArchiveDataType.CLOSING, nextDay )

            for key, nextVal in nextValue.items():
                prevVal = prevValue[ key ]
                diff = nextVal - prevVal
                if diff <= 0:
                    continue
                raiseCounter.count( key )

            counterMonday -= datetime.timedelta(days=7)

        rowsList = []

        prevDay = self.getRecentValidDay( lastMonday )
        nextDay = self.getNextValidDay( lastMonday )
        prevValue = self.data.getData( ArchiveDataType.CLOSING, prevDay )
        nextValue = self.data.getData( ArchiveDataType.CLOSING, nextDay )

        for key, val in raiseCounter.counter.items():
            currAccuracy = val / numOfWeeks

            prevVal = prevValue[ key ]
            nextVal = nextValue[ key ]
            diff = nextVal - prevVal
            pot = diff / prevVal
            moneyLink = self.getMoneyPlLink( key )
            rowsList.append( [key, prevVal, nextVal, pot, currAccuracy, moneyLink] )

        ## sort by accuracy, then by potential
        rowsList.sort(key=lambda x: (x[4], x[3]), reverse=True)

        writer.writerow( columnsList )
        for row in rowsList:
            writer.writerow( row )

        retDataFrame = pandas.DataFrame.from_records( rowsList, columns=columnsList )

        self.logger.debug( "Done" )

        return retDataFrame

    # pylint: disable=R0914
    def calcVariance(self, fromDay: date, toDay: date, outFilePath=None):
        self.logger.debug( "Calculating stock variance in range: %s %s", fromDay, toDay )

        varDict = StockDict()
        tradDict = StockDict()
        currDate = fromDay
        while currDate <= toDay:
#             _LOGGER.debug( "accessing data for dat: %s", currDate )
            openingVal = self.loadData( ArchiveDataType.OPENING, currDate )
            minVal = self.loadData( ArchiveDataType.MIN, currDate )
            maxVal = self.loadData( ArchiveDataType.MAX, currDate )
            closingVal = self.loadData( ArchiveDataType.CLOSING, currDate )
            tradingVal = self.loadData( ArchiveDataType.TRADING, currDate )

            if tradingVal is None:
                currDate += datetime.timedelta(days=1)
                continue

            for key, val in tradingVal.items():
                if val == 0:
                    del openingVal[key]
                    del minVal[key]
                    del maxVal[key]
                    del closingVal[key]

            minDict = StockDict()
            minDict.min( openingVal )
            minDict.min( closingVal )

            maxDict = StockDict()
            maxDict.max( openingVal )
            maxDict.max( closingVal )

            diffDict1 = StockDict.var( maxVal, maxDict.stock )
            diffDict2 = StockDict.var( minVal, minDict.stock )

            dayDict = StockDict()
            dayDict.sum( diffDict1.stock )
            dayDict.sum( diffDict2.stock )

            varDict.sum( dayDict.stock )
            tradDict.sum( tradingVal )

            currDate += datetime.timedelta(days=1)

        dataDict = varDict.stock

        file = outFilePath
        if file is None:
            file = tmp_dir + "out/output_var.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )

        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["reference period:", dates_to_string( [fromDay, toDay] ) ] )
        writer.writerow( ["variance:", ("|maxVal - max(open, close)| / max(open, close) + "
                                        "|minVal - min(open, close)| / min(open, close)") ] )
        writer.writerow( [] )

        columnsList = ["name", "variance", "trading [kPLN]", "link"]

        rowsList = []

        for key, val in dataDict.items():
            moneyLink = self.getMoneyPlLink( key )
            trading = tradDict[ key ]
            val = round( val, 4 )
            rowsList.append( [key, val, trading, moneyLink] )

        ## sort by variance
        rowsList.sort(key=lambda x: x[1], reverse=True)

        writer.writerow( columnsList )
        for row in rowsList:
            writer.writerow( row )

        retDataFrame = pandas.DataFrame.from_records( rowsList, columns=columnsList )

        self.logger.debug( "Done" )

        return retDataFrame

    def calcActivity(self, fromDay: date, toDay: date, outFilePath=None):
        self.logger.debug( "Calculating stock activity in range: %s %s", fromDay, toDay )

        isinDict = self.data.getISINForDate( toDay )
#         isinList = isinDict.values()
        isinItems = isinDict.items()

        dataDict = list()
        dataDict.append( StockDict() )
        dataDict.append( StockDict() )
        dataDict.append( StockDict() )
        dataDict.append( StockDict() )

        pool = multiprocessing.dummy.Pool( 1 )

        currDate = fromDay
        currDate -= datetime.timedelta(days=1)
        while currDate < toDay:
            currDate += datetime.timedelta(days=1)

#             _LOGGER.debug( "accessing data for date: %s", currDate )

#             for ticker, isin in isinDict.items():
#                 intradayData = GpwCurrentStockIntradayData( isin )
#                 dataFrame    = intradayData.getWorksheetForDate( currDate )
#                 if dataFrame is None:
#                     ## no data
#                     continue
#                 priceColumn  = dataFrame["c"]
#                 priceVar     = priceColumn.var()
#                 varDict.add( ticker, priceVar )

            calc = DataLoader( currDate )
            loadedData = calc.load( isinItems, pool )
            for name, dataFrame in loadedData:
                if dataFrame is None:
                    continue

                priceColumn = dataFrame["c"]
                calcRet = VarCalc.calcActivity(priceColumn)
                dataDict[0].add( name, calcRet )

                calcRet = VarCalc.calcChange1(priceColumn)
                dataDict[1].add( name, calcRet )

                volumenColumn = dataFrame["v"]
                calcRet = VarCalc.calcChange2(volumenColumn)
                dataDict[2].add( name, calcRet )

                turnoverColumn = priceColumn * volumenColumn
                calcRet = VarCalc.calcStdDev( turnoverColumn )
                dataDict[3].add( name, calcRet )

#                 calcRet = VarCalc.calcSum(volumenColumn)
#                 dataDict[2].add( name, calcRet )

#             calc = VarCalc( currDate )
#             priceRet  = calc.calculateChange1( "c", isinItems, pool )
# #             ret = calc.calculateStdDev( isinItems, pool )
# #             ret = calc.calculateVar( isinItems, pool )
#             dataDict[0].addDict( priceRet )
#
#             volumeRet = calc.calculateChange2( "v", isinItems, pool )
#             dataDict[1].addDict( volumeRet )

        file = outFilePath
        if file is None:
            file = tmp_dir + "out/output_var2.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )

        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["reference period:", dates_to_string( [fromDay, toDay] ) ] )
        writer.writerow( ["variance:", ("|maxVal - max(open, close)| / max(open, close) + "
                                        "|minVal - min(open, close)| / min(open, close)") ] )
        writer.writerow( [] )

#         columnsList = ["name", "variance"]
        columnsList = ["name", "price activity", "price variance", "volume variance",
                       "turnover stddev", "total volume", "trading [kPLN]", "link"]

        rowsList = []

        for key in dataDict[0].keys():
            moneyLink = self.getMoneyPlLink( key )
#             trading = tradDict[ key ]

            priceAct = dataDict[0][key]
            priceAct = round( priceAct, 4 )

            price = dataDict[1][key]
            price = round( price, 4 )

            volume = dataDict[2][key]
            volume = round( volume, 4 )

            turnover = dataDict[3][key]
            turnover = round( turnover, 4 )

#             volume2 = dataDict[1][key]
#             volume2 = round( volume, 4 )

            rowsList.append( [key, priceAct, price, volume, turnover, 0.0, 0.0, moneyLink] )

        ## sort by variance
        rowsList.sort(key=lambda x: x[1], reverse=True)

        writer.writerow( columnsList )
        for row in rowsList:
            writer.writerow( row )

        retDataFrame = pandas.DataFrame.from_records( rowsList, columns=columnsList )

        self.logger.debug( "Done" )

        return retDataFrame

    # ==========================================================================

    def getRecentValidDay(self, fromDay: date=date.today(), checkGiven=False ):
        if checkGiven is False:
            fromDay -= datetime.timedelta(days=1)
        return self.data.getRecentValidDay( fromDay )

    def getNextValidDay(self, fromDay: date=date.today() ):
        return self.data.getNextValidDay( fromDay )

    def getMoneyPlLink(self, name):
        if self.isinDict is None:
            self.isinDict = self.data.getISIN()
        isin = self.isinDict.get( name )
        if isin is None:
            return ""
        ## money link: https://www.money.pl/gielda/spolki-gpw/PLAGORA00067.html
        moneyLink = "https://www.money.pl/gielda/spolki-gpw/" + isin + ".html"
        return moneyLink

    # ==========================================================================

    def _calcDayOfWeek( self, numOfDay, numOfWeeks=1, lastDay: date=date.today(),
                        outFilePath=None, validDirection=True ):
        # ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dayName = calendar.day_name[ numOfDay ].lower()
        file = outFilePath
        if file is None:
            file = tmp_dir + "out/" + dayName + "_change.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )

        lastValid = self.getRecentValidDay( lastDay )
        weekDay = lastValid.weekday()                                   ## 0 for Monday
        lastValid -= datetime.timedelta(days=weekDay)                   ## move to Monday
        if numOfDay > weekDay:
            ## previous week
            lastValid -= datetime.timedelta(days=7)
        lastValid += datetime.timedelta(days=numOfDay)                  ## move to desired day

        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["last " + dayName + ":", str(lastValid) ] )
        writer.writerow( ["num of weeks:", numOfWeeks ] )
        writer.writerow( [] )

        columnsList = ["name", "opening val", "closing val", "potential", "potential avg", "accuracy", "link"]

        raiseCounter: Dict[ str, int ]    = dict()
        potAvg: Dict[ str, List[float] ]  = dict()
        counterMonday = lastValid

        for _ in range(0, numOfWeeks):
            if validDirection:
                nextDay = self.getNextValidDay( counterMonday )
            else:
                nextDay = self.getRecentValidDay( counterMonday, True )

            ## calc
            prevValue = self.data.getData( ArchiveDataType.OPENING, nextDay )
            nextValue = self.data.getData( ArchiveDataType.CLOSING, nextDay )

            for key, nextVal in nextValue.items():
                prevVal = prevValue[ key ]
                if prevVal == 0:
                    continue
                diff = nextVal - prevVal
                if diff <= 0:
                    continue
                raiseCounter[key] = raiseCounter.get( key, 0 ) + 1
                avgPair: List[ float ] = potAvg.get(key, [0, 0])
                avgPair[0] = avgPair[0] + diff / prevVal
                avgPair[1] = avgPair[1] + 1
                potAvg[ key ] = avgPair

            counterMonday -= datetime.timedelta(days=7)

        rowsList = []

        if validDirection:
            nextDay = self.getNextValidDay( lastValid )
        else:
            nextDay = self.getRecentValidDay( lastValid, True )

        prevValue = self.data.getData( ArchiveDataType.OPENING, nextDay )
        nextValue = self.data.getData( ArchiveDataType.CLOSING, nextDay )

        for key, val in raiseCounter.items():
            currAccuracy = val / numOfWeeks

            prevVal = prevValue.get( key, 0 )
            nextVal = nextValue.get( key, 0 )
            diff = nextVal - prevVal
            pot = 0.0
            if prevVal != 0:
                pot = diff / prevVal
            avgPair = potAvg.get(key, [0, 0])
            avgVal = avgPair[0] / avgPair[1]
            moneyLink = self.getMoneyPlLink( key )

            pot    = round( pot, 4 )
            avgVal = round( avgVal, 4 )

            rowsList.append( [key, prevVal, nextVal, pot, avgVal, currAccuracy, moneyLink] )

        ## sort by accuracy, then by potential
        rowsList.sort(key=lambda x: (x[5], x[3]), reverse=True)

        writer.writerow( columnsList )
        for row in rowsList:
            writer.writerow( row )

        retDataFrame = pandas.DataFrame.from_records( rowsList, columns=columnsList )

        self.logger.debug( "Done" )

        return retDataFrame


StockAnalysis.logger = _LOGGER.getChild(StockAnalysis.__name__)


def dates_to_string(datesList):
    output = ""
    for d in datesList:
        output += str(d) + " "
    return output
