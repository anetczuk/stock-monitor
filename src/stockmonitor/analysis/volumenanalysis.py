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

from stockmonitor import persist
from stockmonitor.analysis.stockanalysisdata import VarCalc, SourceDataLoader, StatsDict
from stockmonitor.analysis.stockanalysisdata import StockAnalysisData
from stockmonitor.analysis.stockanalysis import dates_to_string
from stockmonitor.dataaccess import tmp_dir
from stockmonitor.dataaccess.gpw.gpwintradaydata import GpwCurrentStockIntradayData
from stockmonitor.dataaccess.metastockdata import MetaStockIntradayData


_LOGGER = logging.getLogger(__name__)


## =======================================================================


class VolumenIntradayDataProvider():

    pass


class GpwCurrentIntradayProvider( VolumenIntradayDataProvider ):

    def __init__(self):
        self.accessDate = None

    def setDate(self, date):
        self.accessDate = date

    ## returns list
    def map(self, isinItems, pool):
        calc = SourceDataLoader( self )
        return calc.map( isinItems, pool )

    def load(self, paramsList):
        name, isin = paramsList
        dataFrame  = self._loadData( isin )
        if dataFrame is None:
            return None

        ## columns: c      h      l      o      p           t      v
        priceColumn   = dataFrame[ "c" ]
        volumenColumn = dataFrame[ "v" ]
        frame = { 'name': name, 'price': priceColumn, 'volumen': volumenColumn }
        return pandas.DataFrame( frame )

    def _loadData(self, isin):
        intradayData = GpwCurrentStockIntradayData( isin )
        dataFrame    = intradayData.getWorksheetForDate( self.accessDate )
        return dataFrame


class MetaStockIntradayProvider( VolumenIntradayDataProvider ):

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


class VolumenAnalysis:

    def __init__(self, dataProvider: VolumenIntradayDataProvider, pool=None):
        self.dataProvider: VolumenIntradayDataProvider = dataProvider

        self.forceRecalc    = None
        self.isinItems      = None
        if pool is None:
            pool = multiprocessing.dummy.Pool( 6 )
        self.pool           = pool

    # pylint: disable=R0914
    def calcVolumen( self, fromDay: datetime.date, toDay: datetime.date,
                     outFilePath=None, forceRecalc=False ):
        _LOGGER.debug( "Calculating stock volumen in range: %s %s", fromDay, toDay )

        self.forceRecalc = forceRecalc

        dataDict            = StatsDict()
        isinDict            = self.getISINForDate( toDay )
        self.isinItems      = isinDict.items()

        # === load precalculated data ===

        dataPairList = []
        currDate = fromDay
#         currDate -= datetime.timedelta( 1 )
        while currDate < toDay:
            dayPair = self.getPrecalcData( currDate )
            dataPairList.append( dayPair )
            currDate += datetime.timedelta(days=1)

#             dayDict = dayPair[1]
#             dayDict["ATLANTIS"].printData()
#                 #print( "aaaa:", priceColumn, volumenColumn, volSum, tradingSum )

        lastDayTuple = self.getPrecalcData( currDate )

        # === calculate volumen ===

        validDataNum = 0
        for dataTuple in dataPairList:
            _LOGGER.debug( "calculating results for %s", dataTuple[2] )
            dayData: StatsDict = dataTuple[1]
            dataDict.add( "volumen_sum", dayData )
            dataDict.add( "trading_sum", dayData )
            rawData = dataTuple[0]
            if rawData:
                validDataNum += 1
        validDataNum = max(validDataNum, 1)

        lastDayDict = lastDayTuple[1]

        namesSet = dataDict.keys() | lastDayDict.keys()
        for name in namesSet:
            dataSubdict = dataDict[ name ]

            ## set default values if missing (e.g. in case of no trading in certain stocks)
            dataSubdict.add( "volumen_sum", 0 )
            dataSubdict.add( "trading_sum", 0.0 )

            ## get values
            dataVolumen = dataSubdict.get( "volumen_sum", 0 )
            dataTrading = dataSubdict.get( "trading_sum", 0 )
            dataSubdict["trading_sum"]  = round( dataTrading, 4 )
#             if dataVolumen == 0:
#                 continue

            lastDaySubdict = lastDayDict[ name ]
            lastVolumen = lastDaySubdict.get( "volumen_sum", 0 )
            lastTrading = lastDaySubdict.get( "trading_sum", 0 )
#             if lastVolumen == 0:
#                 continue

            dataVolumenAvg = dataVolumen / validDataNum
            dataSubdict["volumen_avg"]    = round( dataVolumenAvg, 4 )
            dataSubdict["recent_vol_sum"] = lastVolumen

            if dataVolumen != 0:
                potentialVol = lastVolumen / dataVolumenAvg
                dataSubdict["volumen_pot"] = round( potentialVol, 4 )
            else:
                if lastVolumen != 0:
                    dataSubdict["volumen_pot"] = float("inf")
                else:
                    dataSubdict["volumen_pot"] = 0.0

            dataTradingAvg = dataTrading / validDataNum
            dataSubdict["trading_avg"]     = round( dataTradingAvg, 4 )
            dataSubdict["recent_trad_sum"] = round( lastTrading, 4 )

            if dataTrading != 0:
                potentialTrad = lastTrading / dataTradingAvg
                dataSubdict["trading_pot"] = round( potentialTrad, 4 )
            else:
                if lastTrading != 0:
                    dataSubdict["trading_pot"] = float("inf")
                else:
                    dataSubdict["trading_pot"] = 0.0

        ## =========================

        file = outFilePath
        if file is None:
            file = tmp_dir + "out/output_volumen.csv"

        headerList = []
        headerList.append( ["reference period:", dates_to_string( [fromDay, toDay] ) ] )
        headerList.append( ["value_sum:", "sum_value{fromDay, toDay-1}"] )
        headerList.append( ["value_avg:", "value_sum / (toDay-1 - fromDay)"] )
        headerList.append( ["recent_val:", "sum_value{toDay}"] )
        headerList.append( ["value_pot:", "recent_val / value_avg"] )
        headerList.append( [] )

        retDataFrame = dataDict.generateDataFrame( namesSet )

        write_to_csv( file, headerList, retDataFrame )

        _LOGGER.debug( "Done" )

        return retDataFrame

    ## returns list: [raw data, precalc data, date]
    def getPrecalcData(self, currDate):
        _LOGGER.debug( "loading data for: %s", currDate )

        if self.forceRecalc is False:
            dateString = currDate.isoformat()
            picklePath = f"{tmp_dir}data/volumen/{dateString}.pickle"
            dataPair = persist.load_object_simple( picklePath, None )
            if dataPair is None:
                _LOGGER.debug( "no precalculated data found -- precalculating" )
                dataPair = self.precalculateData( currDate )
                persist.store_object_simple(dataPair, picklePath)
        else:
            dataPair = self.precalculateData( currDate )

        return list( dataPair ) + [ currDate ]

    ## returns tuple: (raw data, precalc data)
    def precalculateData(self, currDate):
        ## dataframe wit columns: name, price, volumen

        dataDicts = StatsDict()
        dataframeList = self._loadData( currDate )
        for dataFrame in dataframeList:
            if dataFrame is None:
                continue
            nameColumn = dataFrame['name']
            name = nameColumn.iloc[0]
#                 _LOGGER.debug( "calculating results for: %s %s, len: %s", currDate, name, dataFrame.shape[0] )

            dataSubdict = dataDicts[ name ]

            priceColumn = dataFrame["price"]
            priceSize = priceColumn.shape[0]
            if priceSize < 1:
                ## no data -- skip
                dataSubdict.add( "volumen_sum", 0 )
                dataSubdict.add( "trading_sum", 0 )
                continue

            volumenColumn = dataFrame["volumen"]
#             volumenSize = volumenColumn.shape[0]
#             if volumenSize < 1:
#                 ## no data -- skip
#                 continue

            volSum        = VarCalc.calcSum( volumenColumn )
            tradingColumn = priceColumn * volumenColumn / 1000
            tradingSum    = VarCalc.calcSum( tradingColumn )

            dataSubdict.add( "volumen_sum", volSum )
            dataSubdict.add( "trading_sum", tradingSum )

        return ( dataframeList, dataDicts )

    def _loadData(self, currDate):
        self.dataProvider.setDate( currDate )
        dataframeList = self.dataProvider.map( self.isinItems, self.pool )
        return dataframeList

    ## returns Dict[ name, isin ]
    def getISINForDate( self, toDay ):
        dataProvider = StockAnalysisData()
        return dataProvider.getISINForDate( toDay )

#     def getCurrent( self ):
#         dataProvider = StockAnalysisData()
#         return dataProvider.getISINForDate( toDay )


def calculate_change( dataSeries ):
    dSize = len( dataSeries )
    if dSize < 1:
        return pandas.Series()
    if dSize < 2:
        return pandas.Series( [ 0.0 ] )
    retList = []
    for i in range(1, dSize):
        diff = ( dataSeries[i] / dataSeries[i - 1] - 1.0 ) * 100.0
        retList.append( diff )
    return pandas.Series( retList )


def write_to_csv( file, headerList, dataFrame ):
    dirPath = os.path.dirname( file )
    os.makedirs( dirPath, exist_ok=True )

    with open(file, 'w', encoding="utf-8") as f:
        writer = csv.writer( f )
        for row in headerList:
            writer.writerow( row )

        writer.writerow( dataFrame.columns )
        rowsList = dataFrame.values.tolist()
        rowsList.sort( key=lambda x: x[0], reverse=True )           ## sort
        for row in rowsList:
            writer.writerow( row )
