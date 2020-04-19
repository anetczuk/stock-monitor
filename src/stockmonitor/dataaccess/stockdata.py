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

import csv

from stockmonitor.dataaccess.datatype import DataType
from stockmonitor.dataaccess.gpwdata import GpwData


_LOGGER = logging.getLogger(__name__)


class StockData(object):
    """Abstraction for stock data."""

    logger: logging.Logger = None

    def __init__(self):
        self.dataProvider = GpwData()
        self.stock = dict()

    def getData(self, dataType: DataType, day: date):
        return self.dataProvider.getData( dataType, day )

    def getPrevValidDay(self, day: date ):
        return self.dataProvider.getPrevValidDay( day )

    def getNextValidDay(self, day: date):
        return self.dataProvider.getNextValidDay( day )

    def getISIN(self):
        day = date.today()
        validDay = self.getPrevValidDay(day)
        return self.dataProvider.getData( DataType.ISIN, validDay )


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
        self.currValue = None
        self.currDate  = None

    def loadMin(self, dataType: DataType, fromDay: date, toDay: date):
        self.logger.debug( "Calculating min in range: %s %s", fromDay, toDay )
        currDate = fromDay
        ret = StockDict()
        while currDate <= toDay:
            dayValues = self.data.getData( dataType, currDate )
            ret.min( dayValues )
            currDate += datetime.timedelta(days=1)
        self.minValue = ret.stock
        self.minDate  = [fromDay, toDay]

    def loadMax(self, dataType: DataType, fromDay: date, toDay: date):
        self.logger.debug( "Calculating max in range: %s %s", fromDay, toDay )
        currDate = fromDay
        ret = StockDict()
        while currDate <= toDay:
            dayValues = self.data.getData( dataType, currDate )
            ret.max( dayValues )
            currDate += datetime.timedelta(days=1)
        self.maxValue = ret.stock
        self.maxDate  = [fromDay, toDay]

    def loadCurr(self, dataType: DataType, day: date=date.today(), offset=0):
        currDay = day + datetime.timedelta(days=offset)
        validDay = self.data.getPrevValidDay( currDay )
        self.currValue = self.data.getData( dataType, validDay )
        self.currDate  = [validDay]

    def loadData(self, dataType: DataType, day: date):
        return self.data.getData( dataType, day )

    def calcGreater(self, level, outFilePath=None):
        file = outFilePath
        if file is None:
            file = "../tmp/out/output_raise.csv"
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

    def calcBestRaise(self, level, outFilePath=None):
        self.logger.info( "Calculating best raise for level: %s", level )
        
        file = outFilePath
        if file is None:
            file = "../tmp/out/output_raise.csv"
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
        
        currTrading = self.loadData( DataType.TRADING, self.currDate[0] )

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
            file = "../tmp/out/output_value.csv"
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
        
        currTrading = self.loadData( DataType.TRADING, self.currDate[0] )

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
            file = "../tmp/out/output_raise.csv"
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
        
    def calcWeekend(self, numOfWeeks=1, accuracy=0.7, lastDay: date=date.today(), outFilePath=None):
        file = outFilePath
        if file is None:
            file = "../tmp/out/weekend_change.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )
        
        lastValid = self.getPrevValidDay( lastDay )
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
            prevDay = self.getPrevValidDay(counterMonday)
            nextDay = self.getNextValidDay(counterMonday)
            
            ## calc
            prevValue = self.data.getData( DataType.CLOSING, prevDay )
            nextValue = self.data.getData( DataType.CLOSING, nextDay )
            
            for key, nextVal in nextValue.items():
                prevVal = prevValue[ key ]
                diff = nextVal - prevVal
                if diff <= 0:
                    continue
                raiseCounter.count( key )
                
            counterMonday -= datetime.timedelta(days=7)
        
        rowsList = []

        prevDay = self.getPrevValidDay( lastMonday )
        nextDay = self.getNextValidDay( lastMonday )
        prevValue = self.data.getData( DataType.CLOSING, prevDay )
        nextValue = self.data.getData( DataType.CLOSING, nextDay )
        
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
        rowsList.sort(key=lambda x:(x[4], x[3]), reverse=True)

        for row in rowsList:
            writer.writerow( row )

        self.logger.debug( "Found companies: %s", len(rowsList) )

    # ==========================================================================

    def getPrevValidDay(self, fromDay: date=date.today(), checkGiven=False ):
        if checkGiven is False:
            fromDay -= datetime.timedelta(days=1)
        return self.data.getPrevValidDay( fromDay )
    
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
            file = "../tmp/out/" + dayName + "_change.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )
        
        lastValid = self.getPrevValidDay( lastDay )
        weekDay = lastValid.weekday()                               # 0 for Monday
        dayOffset = weekDay - numOfDay
        lastMonday = lastValid - datetime.timedelta(days=dayOffset)
        
        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["last " + dayName + ":", str(lastMonday) ] )
        writer.writerow( ["num of weeks:", numOfWeeks ] )
        writer.writerow( ["accuracy:", accuracy ] )
        writer.writerow( [] )
        
        writer.writerow( ["name", "opening val", "closing val", "potential", "potential avg", "accuracy", "link"] )
        
        raiseCounter = dict()
        potAvg = dict()
        counterMonday = lastMonday
        
        for _ in range(0, numOfWeeks):
            if validDirection:
                nextDay = self.getNextValidDay( counterMonday )
            else:
                nextDay = self.getPrevValidDay( counterMonday, True )
            
            ## calc
            prevValue = self.data.getData( DataType.OPENING, nextDay )
            nextValue = self.data.getData( DataType.CLOSING, nextDay )
            
            for key, nextVal in nextValue.items():
                prevVal = prevValue[ key ]
                if prevVal == 0:
                    continue
                diff = nextVal - prevVal
                if diff <= 0:
                    continue
                raiseCounter[key] = raiseCounter.get( key, 0 ) + 1
                avgPair = potAvg.get(key, [0, 0])
                avgPair[0] = avgPair[0] + diff / prevVal
                avgPair[1] = avgPair[1] + 1
                potAvg[ key ] = avgPair
                
            counterMonday -= datetime.timedelta(days=7)
        
        rowsList = []

        if validDirection:
            nextDay = self.getNextValidDay( lastMonday )
        else:
            nextDay = self.getPrevValidDay( lastMonday, True )
        
        prevValue = self.data.getData( DataType.OPENING, nextDay )
        nextValue = self.data.getData( DataType.CLOSING, nextDay )
        
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
        rowsList.sort(key=lambda x:(x[5], x[3]), reverse=True)

        for row in rowsList:
            writer.writerow( row )

        self.logger.debug( "Found companies: %s", len(rowsList) )
    

StockAnalysis.logger = _LOGGER.getChild(StockAnalysis.__name__)

