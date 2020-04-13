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

import csv

from stockmonitor.dataaccess.gpwdata import GpwData


_LOGGER = logging.getLogger(__name__)


class StockData(object):
    '''
    classdocs
    '''

    logger = None


    def __init__(self):
        '''
        Constructor
        '''
        self.dataProvider = GpwData()
        self.stock = dict()

    def getLastValidDay(self, day: date):
        return self.dataProvider.getLastValidDay( day )
    
    def getMax(self, day: date):
        self.logger.debug( "getting data from date: %s", day )
        return self.dataProvider.getMax( day )
    
    def getMin(self, day: date):
        self.logger.debug( "getting data from date: %s", day )
        return self.dataProvider.getMin( day )
    
    def getClose(self, day: date):
        return self.dataProvider.getClose( day )
        
    def getVolume(self, day: date):
        self.logger.debug( "getting data from date: %s", day )
        return self.dataProvider.getVolume( day )
        
    def getTurnover(self, day: date):
        self.logger.debug( "getting data from date: %s", day )
        return self.dataProvider.getTurnover( day )
    
    def getISIN(self, day: date):
        return self.dataProvider.getISIN( day )

StockData.logger = _LOGGER.getChild(StockData.__name__)


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
    '''
    classdocs
    '''

    logger = None

    def __init__(self):
        '''
        Constructor
        '''
        self.data = StockData()
        self.isinDict = None
        
        self.minStock  = None
        self.maxStock  = None
        self.currStock = None

    def loadMin(self, fromDay: date, toDay: date):
        self.minStock = self.getMinInRange( fromDay, toDay )
    
    def loadMax(self, fromDay: date, toDay: date):
        self.maxStock = self.getMaxInRange( fromDay, toDay )
        
    def loadCurr(self, day: date=date.today(), offset=0):
        currDay = day + datetime.timedelta(days=offset)
        validDay = self.data.getLastValidDay( currDay )
        self.currStock = self.data.getClose( validDay )
    
    def loadMinTurnover(self, fromDay: date, toDay: date):
        self.logger.debug( "Calculating min in range: %s %s", fromDay, toDay )
        currDate = fromDay
        ret = StockDict()
        while currDate <= toDay:
            dayValues = self.data.getTurnover( currDate )
            ret.min( dayValues )
            currDate += datetime.timedelta(days=1)
        self.minStock = ret.stock
    
    def loadMaxTurnover(self, fromDay: date, toDay: date):
        self.logger.debug( "Calculating min in range: %s %s", fromDay, toDay )
        currDate = fromDay
        ret = StockDict()
        while currDate <= toDay:
            dayValues = self.data.getTurnover( currDate )
            ret.max( dayValues )
            currDate += datetime.timedelta(days=1)
        self.maxStock = ret.stock

    def loadCurrTurnover(self, day: date=date.today(), offset=0):
        currDay = day + datetime.timedelta(days=offset)
        validDay = self.data.getLastValidDay( currDay )
        self.currStock = self.data.getTurnover( validDay )
    
    def loadMaxVolume(self, fromDay: date, toDay: date):
        self.logger.debug( "Calculating min in range: %s %s", fromDay, toDay )
        currDate = fromDay
        ret = StockDict()
        while currDate <= toDay:
            dayValues = self.data.getVolume( currDate )
            ret.max( dayValues )
            currDate += datetime.timedelta(days=1)
        self.maxStock = ret.stock

    def loadCurrVolume(self, day: date=date.today(), offset=0):
        currDay = day + datetime.timedelta(days=offset)
        validDay = self.data.getLastValidDay( currDay )
        self.currStock = self.data.getVolume( validDay )
    
    def calcBestRaise(self, level):
        file = "../tmp/out/output_raise.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )
        
        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["name", "max val", "min val", "curr val", "potential", "link"] )
        for key, val in self.currStock.items():
            maxVal = self.maxStock[ key ]
            minVal = self.minStock[ key ]
            stockDiff = maxVal - minVal
            currDiff = val - minVal
            refLevel = stockDiff * level
            if currDiff < refLevel:
                pot = maxVal / val
                moneyLink = self.getMoneyPlLink( key )
                writer.writerow( [key, maxVal, minVal, val, pot, moneyLink] )
                
    def calcBestValue(self, level):
        self.logger.info( "Calculating best value for level: %s", level )
        
        file = "../tmp/out/output_value.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )
        
        foundCounter = 0;
        
        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["name", "max val", "curr val", "potential", "link"] )
        for key, val in self.currStock.items():
            maxVal = self.maxStock[ key ]
            refLevel = maxVal * level
            if val < refLevel:
                pot = maxVal / val
                moneyLink = self.getMoneyPlLink( key )
                writer.writerow( [key, maxVal, val, pot, moneyLink] )
                foundCounter += 1
                
        self.logger.debug( "Found companies: %s", foundCounter )
    
    def calcBiggestRaise(self, level):
        file = "../tmp/out/output_raise.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )
        
        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["name", "max val", "curr val", "potential", "link"] )
        for key, val in self.currStock.items():
            stockVal = self.maxStock[ key ]
            refLevel = stockVal * level
            if val > refLevel:
                pot = 0
                if stockVal > 0:
                    pot = val / stockVal
                moneyLink = self.getMoneyPlLink( key )
                writer.writerow( [key, stockVal, val, pot, moneyLink] )

    # ==========================================================================
    
    def getMaxInRange(self, fromDay: date, toDay: date):
        self.logger.debug( "Calculating max in range: %s %s", fromDay, toDay )
        currDate = fromDay
        ret = StockDict()
        while currDate <= toDay:
            dayStock = self.data.getMax( currDate )
            ret.max( dayStock )
            currDate += datetime.timedelta(days=1)
        return ret.stock
    
    def getMinInRange(self, fromDay: date, toDay: date):
        self.logger.debug( "Calculating min in range: %s %s", fromDay, toDay )
        currDate = fromDay
        ret = StockDict()
        while currDate <= toDay:
            dayStock = self.data.getMin( currDate )
            ret.min( dayStock )
            currDate += datetime.timedelta(days=1)
        return ret.stock
    
    def getPrevDayStock(self):
        prevDay = date.today() - datetime.timedelta(days=1)
        return self.data.getLastValid( prevDay )
    
    def getISIN(self):
        day = date.today()
        return self.data.getISIN( day )

    def getMoneyPlLink(self, name):
        if self.isinDict is None:
            self.isinDict = self.getISIN()
        isinCode = self.isinDict[ name ]
        ## money link: https://www.money.pl/gielda/spolki-gpw/PLAGORA00067.html
        moneyLink = "https://www.money.pl/gielda/spolki-gpw/" + isinCode + ".html"
        return moneyLink
    
StockAnalysis.logger = _LOGGER.getChild(StockAnalysis.__name__)
