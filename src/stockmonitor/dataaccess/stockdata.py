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

from typing import Dict, List

import csv

from stockmonitor.dataaccess.datatype import ArchiveDataType
from stockmonitor.dataaccess.gpwdata import GpwArchiveData


_LOGGER = logging.getLogger(__name__)

script_dir = os.path.dirname(os.path.realpath(__file__))

tmp_dir = script_dir + "/../../../tmp/"


class StockData(object):
    """Abstraction for stock data."""

    logger: logging.Logger = None

    def __init__(self):
        self.dataProvider = GpwArchiveData()
        self.stock = dict()

    def getData(self, dataType: ArchiveDataType, day: date):
        return self.dataProvider.getData( dataType, day )

    def getRecentValidDay(self, day: date ):
        return self.dataProvider.getRecentValidDay( day )

    def getNextValidDay(self, day: date):
        return self.dataProvider.getNextValidDay( day )

    def getISIN(self):
        _LOGGER.info("loading recent ISIN data" )
        day = date.today() - datetime.timedelta(days=1)
        validDay = self.getRecentValidDay(day)
        return self.dataProvider.getData( ArchiveDataType.ISIN, validDay )


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

    def loadMin(self, dataType: ArchiveDataType, fromDay: date, toDay: date):
        self.logger.debug( "Calculating min in range: %s %s", fromDay, toDay )
        currDate = fromDay
        ret = StockDict()
        while currDate <= toDay:
            dayValues = self.data.getData( dataType, currDate )
            ret.min( dayValues )
            currDate += datetime.timedelta(days=1)
        self.minValue = ret.stock
        self.minDate  = [fromDay, toDay]

    def loadMax(self, dataType: ArchiveDataType, fromDay: date, toDay: date):
        self.logger.debug( "Calculating max in range: %s %s", fromDay, toDay )
        currDate = fromDay
        ret = StockDict()
        while currDate <= toDay:
            dayValues = self.data.getData( dataType, currDate )
            ret.max( dayValues )
            currDate += datetime.timedelta(days=1)
        self.maxValue = ret.stock
        self.maxDate  = [fromDay, toDay]

    def loadSum(self, dataType: ArchiveDataType, fromDay: date, toDay: date):
        self.logger.debug( "Calculating sum in range: %s %s", fromDay, toDay )
        currDate = fromDay
        ret = StockDict()
        while currDate <= toDay:
            _LOGGER.debug( "accessing data for dat: %s", currDate )
            dayValues = self.data.getData( dataType, currDate )
            ret.sum( dayValues )
            currDate += datetime.timedelta(days=1)
        self.sumValue = ret.stock
        self.sumDate  = [fromDay, toDay]

    def loadCurr(self, dataType: ArchiveDataType, day: date=date.today(), offset=0):
        currDay = day + datetime.timedelta(days=offset)
        validDay = self.data.getRecentValidDay( currDay )
        self.currValue = self.data.getData( dataType, validDay )
        self.currDate  = [validDay]

    def loadData(self, dataType: ArchiveDataType, day: date):
        return self.data.getData( dataType, day )

    def calcGreatestSum(self, outFilePath=None):
        file = outFilePath
        if file is None:
            file = tmp_dir + "out/output_raise.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )

        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["reference period:", self.listDatesToString(self.sumDate) ] )
        writer.writerow( [] )

        writer.writerow( ["name", "trading [kPLN]", "link"] )

        rowsList = []

        for key, val in self.sumValue.items():
            moneyLink = self.getMoneyPlLink( key )
            rowsList.append( [key, val, moneyLink] )

        ## sort by trading
        rowsList.sort(key=lambda x: x[1], reverse=True)

        for row in rowsList:
            writer.writerow( row )

        self.logger.debug( "Found companies: %s", len(rowsList) )

    def calcGreater(self, level, outFilePath=None):
        file = outFilePath
        if file is None:
            file = tmp_dir + "out/output_raise.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )

        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["reference period:", self.listDatesToString(self.currDate) ] )
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

    # pylint: disable=R0914
    def calcBestRaise(self, level, outFilePath=None):
        self.logger.info( "Calculating best raise for level: %s", level )

        file = outFilePath
        if file is None:
            file = tmp_dir + "out/output_raise.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )

        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["max period:", self.listDatesToString(self.maxDate) ] )
        writer.writerow( ["min period:", self.listDatesToString(self.minDate) ] )
        writer.writerow( ["reference period:", self.listDatesToString(self.currDate) ] )
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
        writer.writerow( ["max period:", self.listDatesToString(self.maxDate) ] )
        writer.writerow( ["reference period:", self.listDatesToString(self.currDate) ] )
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
        writer.writerow( ["max period:", self.listDatesToString(self.maxDate) ] )
        writer.writerow( ["reference period:", self.listDatesToString(self.currDate) ] )
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

    def calcMonday(self, numOfWeeks=1, accuracy=0.7, lastDay: date=date.today(), outFilePath=None):
        self.logger.info( "Calculating Monday stock" )
        self._calcDayOfWeek( 0, numOfWeeks, accuracy, lastDay, outFilePath, True )

    def calcFriday(self, numOfWeeks=1, accuracy=0.7, lastDay: date=date.today(), outFilePath=None):
        self.logger.info( "Calculating Friday stock" )
        self._calcDayOfWeek( 4, numOfWeeks, accuracy, lastDay, outFilePath, False )

    # pylint: disable=R0914
    def calcWeekend(self, numOfWeeks=1, accuracy=0.7, lastDay: date=date.today(), outFilePath=None):
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
        writer.writerow( ["accuracy:", accuracy ] )
        writer.writerow( [] )

        writer.writerow( ["name", "friday val", "monday val", "potential", "accuracy", "link"] )

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
            if currAccuracy < accuracy:
                continue

            prevVal = prevValue[ key ]
            nextVal = nextValue[ key ]
            diff = nextVal - prevVal
            pot = diff / prevVal
            moneyLink = self.getMoneyPlLink( key )
            rowsList.append( [key, prevVal, nextVal, pot, currAccuracy, moneyLink] )

        ## sort by accuracy, then by potential
        rowsList.sort(key=lambda x: (x[4], x[3]), reverse=True)

        for row in rowsList:
            writer.writerow( row )

        self.logger.debug( "Found companies: %s", len(rowsList) )

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
            file = tmp_dir + "out/output_raise.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )

        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["reference period:", self.listDatesToString(self.sumDate) ] )
        writer.writerow( ["formula:", "|maxVal - max(open, close)| / max(open, close) + |minVal - min(open, close)| / min(open, close)"] )
        writer.writerow( [] )

        writer.writerow( ["name", "variance", "trading [kPLN]", "link"] )

        rowsList = []

        for key, val in dataDict.items():
            moneyLink = self.getMoneyPlLink( key )
            trading = tradDict[ key ]
            rowsList.append( [key, val, trading, moneyLink] )

        ## sort by variance
        rowsList.sort(key=lambda x: x[1], reverse=True)

        for row in rowsList:
            writer.writerow( row )

        self.logger.debug( "Found companies: %s", len(rowsList) )

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
        isinCode = self.isinDict.get( name )
        if isinCode is None:
            return ""
        ## money link: https://www.money.pl/gielda/spolki-gpw/PLAGORA00067.html
        moneyLink = "https://www.money.pl/gielda/spolki-gpw/" + isinCode + ".html"
        return moneyLink

    def listDatesToString(self, datesList):
        output = ""
        for d in datesList:
            output += str(d) + " "
        return output

    # ==========================================================================

    def _calcDayOfWeek( self, numOfDay, numOfWeeks=1, accuracy=0.7, lastDay: date=date.today(), outFilePath=None, validDirection=True ):
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
        writer.writerow( ["accuracy:", accuracy ] )
        writer.writerow( [] )

        writer.writerow( ["name", "opening val", "closing val", "potential", "potential avg", "accuracy", "link"] )

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
            if currAccuracy < accuracy:
                continue

            prevVal = prevValue.get( key, 0 )
            nextVal = nextValue.get( key, 0 )
            diff = nextVal - prevVal
            pot = 0
            if prevVal != 0:
                pot = diff / prevVal
            avgPair = potAvg.get(key, [0, 0])
            avgVal = avgPair[0] / avgPair[1]
            moneyLink = self.getMoneyPlLink( key )
            rowsList.append( [key, prevVal, nextVal, pot, avgVal, currAccuracy, moneyLink] )

        ## sort by accuracy, then by potential
        rowsList.sort(key=lambda x: (x[5], x[3]), reverse=True)

        for row in rowsList:
            writer.writerow( row )

        self.logger.debug( "Found companies: %s", len(rowsList) )


StockAnalysis.logger = _LOGGER.getChild(StockAnalysis.__name__)
