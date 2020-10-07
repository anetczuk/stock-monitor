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
import multiprocessing.dummy

import csv
import pandas

from stockmonitor.dataaccess import tmp_dir
from stockmonitor.dataaccess.stockanalysisdata import StockDict, VarCalc, SourceDataLoader
from stockmonitor.dataaccess.stockanalysisdata import StockData
from stockmonitor.dataaccess.gpw.gpwintradaydata import GpwCurrentStockIntradayData
from stockmonitor.dataaccess.metastockdata import MetaStockIntradayData
from stockmonitor.dataaccess.stockanalysis import dates_to_string


_LOGGER = logging.getLogger(__name__)


## =======================================================================


# class MinMaxAnalysis:
#
#     def __init__(self):
#         today = datetime.datetime.now().date()
#         self.minDate  = [ today, today ]
#         self.maxDate  = [ today, today ]
#         self.currDate = [ today, today ]
#
#     def calcPotentials(self, outFilePath=None):
#         _LOGGER.info( "Calculating potential" )
#
#         if outFilePath is None:
#             outFilePath = tmp_dir + "out/output_potentials.csv"
#         dirPath = os.path.dirname( outFilePath )
#         os.makedirs( dirPath, exist_ok=True )
#
#         writer = csv.writer(open(outFilePath, 'w'))
#         writer.writerow( ["min period:", dates_to_string(self.minDate) ] )
#         writer.writerow( ["max period:", dates_to_string(self.maxDate) ] )
#         writer.writerow( ["recent val date:", dates_to_string(self.currDate) ] )
#         writer.writerow( ["potential:", "(max - curr) / max"] )
#         writer.writerow( ["relative:",  "(max - curr) / (max - min)"] )
#         writer.writerow( ["pot raise[%]:",  "(max / curr - 1.0) * 100%"] )
#         writer.writerow( [] )
#
#         columnsList = [ "name", "min val", "max val", "curr val", "trading[k]",
#                         "potential", "relative", "pot raise[%]", "link" ]
#         rowsList = []
#
#         currTrading = self.loadData( ArchiveDataType.TRADING, self.currDate[0] )
#
#         for key, currVal in self.currValue.items():
#             maxVal = self.maxValue.get( key )
#             if maxVal is None or maxVal == 0:
#                 ## new stock, ignore
#                 continue
#             minVal = self.minValue[ key ]
#             tradingVal = currTrading[ key ]
#             raiseVal = maxVal - currVal
#             potVal = raiseVal / maxVal
#             stockDiff = maxVal - minVal
#             relVal = 0
#             if stockDiff != 0:
#                 relVal = raiseVal / stockDiff
#             potRaise = (maxVal / currVal - 1.0) * 100.0
#             moneyLink = self.getMoneyPlLink( key )
#             potVal   = round( potVal, 4 )
#             relVal   = round( relVal, 4 )
#             potRaise = round( potRaise, 2 )
#             rowsList.append( [key, minVal, maxVal, currVal, tradingVal, potVal, relVal, potRaise, moneyLink] )
#
#         writer.writerow( columnsList )
#         for row in rowsList:
#             writer.writerow( row )
#
#         retDataFrame = pandas.DataFrame.from_records( rowsList, columns=columnsList )
#
#         self.logger.debug( "Done" )
#
#         return retDataFrame


class GpwCurrentIntradayProvider():

    def __init__(self):
        self.accessDate = None

    def setDate(self, date):
        self.accessDate = date

    def map(self, isinItems, pool):
        calc = SourceDataLoader( self )
        return calc.map( isinItems, pool )

    def load(self, paramsList):
        name, isin   = paramsList
        intradayData = GpwCurrentStockIntradayData( isin )
        dataFrame    = intradayData.getWorksheetForDate( self.accessDate )
        if dataFrame is None:
            return (name, dataFrame)

        ## columns: c      h      l      o      p           t      v
        priceColumn   = dataFrame[ "c" ]
        volumenColumn = dataFrame[ "v" ]
        frame = { 'price': priceColumn, 'volumen': volumenColumn }
        result = pandas.DataFrame( frame )

        return (name, result)


class MetaStockIntradayProvider():

    def __init__(self):
        self.accessDate = None
        self.intradayData = MetaStockIntradayData()

    def setDate(self, date):
        self.accessDate = date

    def map(self, isinItems, pool):
        dataFrame = pool.apply( self._loadData )
        retList = list()
        for name, _ in isinItems:
            nameData = self._getData( dataFrame, name )
            retList.append( nameData )
        return retList

    def load(self, paramsList):
        dataFrame    = self._loadData()
        name         = paramsList[0]
        if dataFrame is None:
            return (name, dataFrame)
        return self._getData( dataFrame, name )

    def _loadData(self):
        return self.intradayData.getWorksheetForDate( self.accessDate )

    def _getData(self, dataFrame, name ):
        nameData = dataFrame[ dataFrame["name"] == name ]
        nameData.reset_index( drop=True, inplace=True )

        ## columns: name  unknown_1      date    time  kurs_otw       max       min      kurs  obrot  unknown_2
        priceColumn   = nameData[ "kurs" ]
        volumenColumn = nameData[ "obrot" ]
        frame = { 'price': priceColumn, 'volumen': volumenColumn }
        result = pandas.DataFrame( frame )
        return (name, result)


class ActivityAnalysis:

    def __init__(self, dataProvider):
        self.dataProvider = dataProvider

    # pylint: disable=R0914
    def calcActivity(self, fromDay: datetime.date, toDay: datetime.date, thresholdPercent, outFilePath=None):
        _LOGGER.debug( "Calculating stock activity in range: %s %s", fromDay, toDay )

        isinDict = self.getISINForDate( toDay )
#         isinList = isinDict.values()
        isinItems = isinDict.items()

        dataDicts = list()
        dataDicts.append( StockDict() )
        dataDicts.append( StockDict() )
        dataDicts.append( StockDict() )
        dataDicts.append( StockDict() )
        dataDicts.append( StockDict() )
        dataDicts.append( StockDict() )
        dataDicts.append( StockDict() )

        pool = multiprocessing.dummy.Pool( 6 )

        currDate = fromDay
        currDate -= datetime.timedelta(days=1)
        while currDate < toDay:
            currDate += datetime.timedelta(days=1)

            self.dataProvider.setDate( currDate )
            loadedData = self.dataProvider.map( isinItems, pool )

            for name, dataFrame in loadedData:
                if dataFrame is None:
                    continue

                _LOGGER.debug( "calculating results for: %s %s, len: %s", currDate, name, dataFrame.shape[0] )

                priceColumn = dataFrame["price"]
                calcRet = VarCalc.calcChange3(priceColumn, thresholdPercent)
                dataDicts[0].add( name, calcRet[1] )                                ## price activity

                priceChangeColumn = calculate_change( priceColumn )
                calcRet = priceChangeColumn.sum()
                dataDicts[1].add( name, calcRet )                                   ## price change sum

                calcRet = priceChangeColumn.std() * len( priceColumn )
                dataDicts[2].add( name, calcRet )                                   ## price change deviation

                volumenColumn = dataFrame["volumen"]
                turnoverColumn = priceColumn * volumenColumn
                calcRet = turnoverColumn.std()
                dataDicts[4].add( name, calcRet )                                   ## turnover

                calcRet = VarCalc.calcSum(volumenColumn)
                dataDicts[5].add( name, calcRet )                                   ## total volume

                tradingColumn = priceColumn * volumenColumn / 1000
                calcRet = VarCalc.calcSum( tradingColumn )
                dataDicts[6].add( name, calcRet )                                   ## trading

        file = outFilePath
        if file is None:
            file = tmp_dir + "out/output_activity.csv"
        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )

        writer = csv.writer(open(file, 'w'))
        writer.writerow( ["reference period:", dates_to_string( [fromDay, toDay] ) ] )
        writer.writerow( ["price activity:", ("count( local_max - local_min > threshold )") ] )
        writer.writerow( ["price  change deviation::", ("price_change.stddev * len( price_change )") ] )
        writer.writerow( [] )

        columnsList = [ "name", "price activity",
                        "price change sum", "price change deviation",
                        "total volume", "trading [kPLN]" ]

        rowsList = []

        for key in dataDicts[0].keys():
#             trading = tradDict[ key ]

            priceAct = dataDicts[0][key]
            #priceAct = round( priceAct, 4 )

            priceChangeAvg = dataDicts[1][key]
            priceChangeAvg = round( priceChangeAvg, 4 )

            priceChangeVar = dataDicts[2][key]
            priceChangeVar = round( priceChangeVar, 4 )

            volumeSum = dataDicts[5][key]
            volumeSum = round( volumeSum, 4 )

            tradingSum = dataDicts[6][key]
            tradingSum = round( tradingSum, 4 )

            rowsList.append( [key, priceAct, priceChangeAvg, priceChangeVar, volumeSum, tradingSum] )

        ## sort by variance
        rowsList.sort(key=lambda x: x[1], reverse=True)

        writer.writerow( columnsList )
        for row in rowsList:
            writer.writerow( row )

        retDataFrame = pandas.DataFrame.from_records( rowsList, columns=columnsList )

        _LOGGER.debug( "Done" )

        return retDataFrame

    ## returns Dict[ name, isin ]
    def getISINForDate( self, toDay ):
        isinProvider = StockData()
        return isinProvider.getISINForDate( toDay )


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
