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
import math
import multiprocessing.dummy

import csv
import pandas

from stockmonitor import persist
from stockmonitor.dataaccess import tmp_dir
from stockmonitor.dataaccess.stockanalysisdata import VarCalc, SourceDataLoader, StatsDict
from stockmonitor.dataaccess.stockanalysisdata import StockData
from stockmonitor.dataaccess.gpw.gpwintradaydata import GpwCurrentStockIntradayData
from stockmonitor.dataaccess.metastockdata import MetaStockIntradayData
from stockmonitor.dataaccess.stockanalysis import dates_to_string


_LOGGER = logging.getLogger(__name__)


## =======================================================================


class GpwCurrentIntradayProvider():

    def __init__(self):
        self.accessDate = None

    def setDate(self, date):
        self.accessDate = date

    ## returns list
    def map(self, isinItems, pool):
        calc = SourceDataLoader( self )
        return calc.map( isinItems, pool )

    def load(self, paramsList):
        name, isin   = paramsList
        intradayData = GpwCurrentStockIntradayData( isin )
        dataFrame    = intradayData.getWorksheetForDate( self.accessDate )
        if dataFrame is None:
            return None

        ## columns: c      h      l      o      p           t      v
        priceColumn   = dataFrame[ "c" ]
        volumenColumn = dataFrame[ "v" ]
        frame = { 'name': name, 'price': priceColumn, 'volumen': volumenColumn }
        return pandas.DataFrame( frame )


class MetaStockIntradayProvider():

    def __init__(self):
        self.accessDate = None
        self.intradayData = MetaStockIntradayData()

    def setDate(self, date):
        self.accessDate = date

    ## returns list
    def map(self, isinItems, pool):
        dataFrame = pool.apply( self._loadData )
        if dataFrame is None:
            return []

        retLsit = []
#         subFrame = dataFrame[ ["name", "kurs", "obrot"] ]
        subFrame = dataFrame.rename( columns={ 'kurs': 'price', 'obrot': 'volumen' } )
        for name, _ in isinItems:
            nameData = subFrame[ subFrame["name"].eq( name ) ]
            if nameData.empty:
                continue
            nameData.reset_index( drop=True, inplace=True )
            retLsit.append( nameData )
        return retLsit

    def load(self, paramsList):
        dataFrame = self._loadData()
        name      = paramsList[0]
        if dataFrame is None:
            return None
        return self._getData( dataFrame, name )

    def _loadData(self):
        return self.intradayData.getWorksheetForDate( self.accessDate )

    def _getData(self, dataFrame, name ):
        nameData = dataFrame[ dataFrame["name"] == name ]
        if nameData.empty:
            return None
        nameData.reset_index( drop=True, inplace=True )

        ## columns: name  unknown_1      date    time  kurs_otw       max       min      kurs  obrot  unknown_2
        priceColumn   = nameData[ "kurs" ]
        volumenColumn = nameData[ "obrot" ]
        frame = { 'name': name, 'price': priceColumn, 'volumen': volumenColumn }
        return pandas.DataFrame( frame )


class ActivityAnalysis:

    def __init__(self, dataProvider):
        self.dataProvider = dataProvider

    # pylint: disable=R0914
    def calcActivity( self, fromDay: datetime.date, toDay: datetime.date, thresholdPercent,
                      outFilePath=None, forceRecalc=False ):
        _LOGGER.debug( "Calculating stock activity in range: %s %s", fromDay, toDay )

        pool = multiprocessing.dummy.Pool( 6 )

        dataDicts = StatsDict()
        isinDict = self.getISINForDate( toDay )
        isinItems = isinDict.items()

        currDate = fromDay
        currDate -= datetime.timedelta(days=1)
        while currDate < toDay:
            currDate += datetime.timedelta(days=1)

            _LOGGER.debug( "loading data for: %s", currDate )

            if forceRecalc is False:
                dateString = currDate.isoformat()
                picklePath = tmp_dir + "data/activity/%s.pickle" % dateString
                dataframeList = persist.load_object_simple( picklePath, None )
                if dataframeList is None:
                    self.dataProvider.setDate( currDate )
                    dataframeList = self.dataProvider.map( isinItems, pool )
                    persist.store_object_simple(dataframeList, picklePath)
            else:
                self.dataProvider.setDate( currDate )
                dataframeList = self.dataProvider.map( isinItems, pool )

            _LOGGER.debug( "calculating results for: %s", currDate )
            self.calculateData( dataframeList, thresholdPercent, dataDicts )

        namesSet = dataDicts.keys()
        for name in namesSet:
            dataSubdict = dataDicts[ name ]
            minVal      = dataSubdict["min price"]
            maxVal      = dataSubdict["max price"]
            currVal     = dataSubdict["curr price"]
            if currVal == 0:
                continue

            raiseVal = maxVal - currVal
            potVal = raiseVal / maxVal
            stockDiff = maxVal - minVal
            relVal = 0.0
            if stockDiff != 0:
                relVal = raiseVal / stockDiff
            potRaise = (maxVal / currVal - 1.0) * 100.0
            potVal   = round( potVal, 4 )
            relVal   = round( relVal, 4 )
            potRaise = round( potRaise, 2 )

            dataSubdict["potential"]   = potVal
            dataSubdict["relative"]    = relVal
            dataSubdict["pot raise %"] = potRaise

            val = dataSubdict["price change sum"]
            dataSubdict["price change sum"] = round( val, 4 )

            val = dataSubdict["price change deviation"]
            dataSubdict["price change deviation"] = round( val, 4 )

            val = dataSubdict["trading [kPLN]"]
            dataSubdict["trading [kPLN]"] = round( val, 4 )

        ## =========================

        file = outFilePath
        if file is None:
            file = tmp_dir + "out/output_activity.csv"

        headerList = list()
        headerList.append( ["reference period:", dates_to_string( [fromDay, toDay] ) ] )
        headerList.append( ["potential:", "(max - curr) / max"] )
        headerList.append( ["relative:",  "(max - curr) / (max - min)"] )
        headerList.append( ["pot raise[%]:",  "(max / curr - 1.0) * 100%"] )
        headerList.append( ["price activity:", ("count( local_max - local_min > threshold )") ] )
        headerList.append( ["price change deviation:", ("price_change.stddev * len( price_change )") ] )
        headerList.append( [] )

        retDataFrame = dataDicts.generateDataFrame( namesSet )

        write_to_csv( file, headerList, retDataFrame )

        _LOGGER.debug( "Done" )

        return retDataFrame

    def calculateData(self, dataframeList, thresholdPercent, dataDicts):
        for dataFrame in dataframeList:
            if dataFrame is None:
                continue
            nameColumn = dataFrame['name']
            name = nameColumn.iloc[0]
#                 _LOGGER.debug( "calculating results for: %s %s, len: %s", currDate, name, dataFrame.shape[0] )

            priceColumn = dataFrame["price"]
            priceSize = priceColumn.shape[0]
            if priceSize < 1:
                ## no data -- skip
                continue

            dataSubdict = dataDicts[ name ]

            minValue = priceColumn.min()
            if math.isnan( minValue ) is False:
                dataSubdict.minValue( "min price", minValue )                                  ## min value

            maxValue = priceColumn.max()
            if math.isnan( maxValue ) is False:
                dataSubdict.maxValue( "max price", maxValue )                                  ## max value

            dataSubdict["curr price"] = priceColumn.iloc[ priceSize - 1 ]

            volumenColumn = dataFrame["volumen"]
            tradingColumn = priceColumn * volumenColumn / 1000
            calcRet = VarCalc.calcSum( tradingColumn )
            dataSubdict.add( "trading [kPLN]", calcRet )                                   ## trading

            dataSubdict["potential"]   = 0.0
            dataSubdict["relative"]    = 0.0
            dataSubdict["pot raise %"] = 0.0

            calcRet = VarCalc.calcChange3(priceColumn, thresholdPercent)
            dataSubdict.add( "price activity", calcRet[1] )                           ## price activity

            priceChangeColumn = calculate_change( priceColumn )
            calcRet = priceChangeColumn.sum()
            dataSubdict.add( "price change sum", calcRet )                            ## price change sum

            calcRet = priceChangeColumn.std() * len( priceColumn )
            if math.isnan( calcRet ):
                calcRet = 0.0
            dataSubdict.add( "price change deviation", calcRet )                      ## price change deviation

    def calculateDataDict(self, dataframeList, thresholdPercent):
        dataDicts = StatsDict()

        for dataFrame in dataframeList:
            if dataFrame is None:
                continue
            nameColumn = dataFrame['name']
            name = nameColumn.iloc[0]
#                 _LOGGER.debug( "calculating results for: %s %s, len: %s", currDate, name, dataFrame.shape[0] )

            priceColumn = dataFrame["price"]
            priceSize = priceColumn.shape[0]
            if priceSize < 1:
                ## no data -- skip
                continue

            dataSubdict = dataDicts[ name ]

            minValue = priceColumn.min()
            if math.isnan( minValue ) is False:
                dataSubdict["min price"] = minValue                                  ## min value

            maxValue = priceColumn.max()
            if math.isnan( maxValue ) is False:
                dataSubdict["max price"] = maxValue                                  ## max value

            dataSubdict["curr price"] = priceColumn.iloc[ priceSize - 1 ]

            volumenColumn = dataFrame["volumen"]
            tradingColumn = priceColumn * volumenColumn / 1000
            calcRet = VarCalc.calcSum( tradingColumn )
            dataSubdict["trading [kPLN]"] = calcRet                                   ## trading

            dataSubdict["potential"]   = 0.0
            dataSubdict["relative"]    = 0.0
            dataSubdict["pot raise %"] = 0.0

            calcRet = VarCalc.calcChange3(priceColumn, thresholdPercent)
            dataSubdict["price activity"] = calcRet[1]                           ## price activity

            priceChangeColumn = calculate_change( priceColumn )
            calcRet = priceChangeColumn.sum()
            dataSubdict["price change sum"] = calcRet                            ## price change sum

            calcRet = priceChangeColumn.std() * len( priceColumn )
            if math.isnan( calcRet ):
                calcRet = 0.0
            dataSubdict["price change deviation"] = calcRet                      ## price change deviation

        return dataDicts

    ## returns Dict[ name, isin ]
    def getISINForDate( self, toDay ):
        dataProvider = StockData()
        return dataProvider.getISINForDate( toDay )

#     def getCurrent( self ):
#         dataProvider = StockData()
#         return dataProvider.getISINForDate( toDay )


def calculate_change( dataSeries ):
    dSize = len( dataSeries )
    if dSize < 1:
        return pandas.Series()
    if dSize < 2:
        return pandas.Series( [ 0.0 ] )
    retList = list()
    for i in range(1, dSize):
        diff = ( dataSeries[i] / dataSeries[i - 1] - 1.0 ) * 100.0
        retList.append( diff )
    return pandas.Series( retList )


def write_to_csv( file, headerList, dataFrame ):
    dirPath = os.path.dirname( file )
    os.makedirs( dirPath, exist_ok=True )

    with open(file, 'w') as f:
        writer = csv.writer( f )
        for row in headerList:
            writer.writerow( row )

        writer.writerow( dataFrame.columns )
        rowsList = dataFrame.values.tolist()
        rowsList.sort( key=lambda x: x[0], reverse=True )           ## sort
        for row in rowsList:
            writer.writerow( row )
