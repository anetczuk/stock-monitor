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

import pandas
import numpy

from stockdataaccess import persist
from stockdataaccess.dataaccess import TMP_DIR
from stockdataaccess.dataaccess.datatype import StockDataType
from stockdataaccess.dataaccess.gpw.gpwintradaydata import GpwCurrentStockIntradayData
from stockdataaccess.dataaccess.metastockdata import MetaStockIntradayData

from stockmonitor.analysis import write_to_csv
from stockmonitor.analysis.stockanalysisdata import VarCalc, SourceDataLoader, StatsDict
from stockmonitor.analysis.stockanalysisdata import StockAnalysisData
from stockmonitor.analysis.stockanalysis import dates_to_string


_LOGGER = logging.getLogger(__name__)


## =======================================================================


class ActivityIntradayDataProvider():

    def __init__(self):
        super().__init__()
        self.refDataProvider = None

    def getReferenceValue(self, name ):
        if self.refDataProvider is None:
            return None
        ticker    = self.refDataProvider.getTickerFieldByName( name )
        if ticker is None:
            return None
        dataRow    = self.refDataProvider.getRowByTicker( ticker )
        colIndex   = self.refDataProvider.getColumnIndex( StockDataType.RECENT_VALUE )
        stockValue = dataRow.iloc[ colIndex ]
#         print("wwwwwwwwwwwwww:\n", dataRow)
#         print("xxxxxxxxxxxxxx:", name, ticker, stockValue)
        return stockValue


class GpwCurrentIntradayProvider( ActivityIntradayDataProvider ):

    def __init__(self):
        super().__init__()
        self.accessDate = None

    def setDate(self, date):
        self.accessDate = date

#     def getReferenceValue(self, name ):
    def getReferenceValue(self, _ ):
        ## intraday provider already current stock values
        return None

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


class MetaStockIntradayProvider( ActivityIntradayDataProvider ):

    def __init__(self):
        super().__init__()
        self.accessDate      = None
        self.intradayData    = MetaStockIntradayData()
        self.refDataProvider = None

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
        return self.intradayData.accessWorksheetForDate( self.accessDate )

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

## =========================================================================


class ActivityAnalysis:

    def __init__(self, dataProvider: ActivityIntradayDataProvider, pool=None):
        self.dataProvider: ActivityIntradayDataProvider = dataProvider

        self.forceRecalc    = None
        self.isinItems      = None
        self.thresholdPrcnt = None
        if pool is None:
            pool = multiprocessing.dummy.Pool( 6 )
        self.pool           = pool

    # pylint: disable=R0914
    def calcActivity( self, fromDay: datetime.date, toDay: datetime.date, thresholdPercent,
                      outFilePath=None, forceRecalc=False ) -> pandas.DataFrame:
        _LOGGER.debug( "Calculating stock activity in range: %s %s", fromDay, toDay )

        self.forceRecalc = forceRecalc

        overall_stats       = StatsDict()
        isinDict            = self.getISINForDate( toDay )
        self.isinItems      = isinDict.items()
        self.thresholdPrcnt = thresholdPercent

        # === load precalculated data ===

        precalc_data_list = []
        currDate = fromDay
        currDate -= datetime.timedelta(days=1)
        while currDate < toDay:
            currDate += datetime.timedelta(days=1)
            dataTuple  = self.getPrecalcData( currDate )
            precalc_data_list.append( dataTuple )

        # === calculate activity ===

        for precalc_day_data in precalc_data_list:
            day_data                  = precalc_day_data[2]
            day_stock_list            = precalc_day_data[0]
            day_stats_dict: StatsDict = precalc_day_data[1]
            _LOGGER.debug( "calculating results for %s", day_data )
            self.calculateActivityForDay( day_stock_list, day_stats_dict, thresholdPercent, overall_stats )

        day_delta = toDay - fromDay
        days_num  = day_delta.days + 1

        namesSet = overall_stats.keys()
        for name in namesSet:
            dataSubdict = overall_stats[ name ]
            minVal      = dataSubdict["min price"]
            maxVal      = dataSubdict["max price"]
            currVal     = dataSubdict["ref price"]
            refVal      = self.dataProvider.getReferenceValue( name )
            if refVal is not None:
                dataSubdict["ref price"] = refVal
                currVal = refVal
            if currVal in (0, '-'):
                continue

            raiseVal  = 0
            try:
                raiseVal  = maxVal - currVal
            # pylint: disable=W0212
            except numpy.core._exceptions.UFuncTypeError:
                _LOGGER.warning( "invalid data '%s' and '%s'", maxVal, currVal )
                raise

            potVal    = raiseVal / maxVal
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
            dataSubdict["trading [kPLN]"]     = round( val, 4 )
            dataSubdict["trading/day [kPLN]"] = round( val / days_num, 4 )

        ## =========================

        file = outFilePath
        if file is None:
            file = TMP_DIR + "out/output_activity.csv"

        refValueDate = toDay
        if self.dataProvider.refDataProvider is not None:
            refValueDate = datetime.datetime.today().date()

        headerList = []
        headerList.append( ["analysis period:", dates_to_string( [fromDay, toDay] ) ] )
        headerList.append( ["reference value date:", str( refValueDate ) ] )
        headerList.append( ["potential:", "(max - ref) / max"] )
        headerList.append( ["relative:",  "(max - ref) / (max - min)"] )
        headerList.append( ["pot raise[%]:",  "(max / ref - 1.0) * 100%"] )
        headerList.append( ["price activity:", ("count( local_max - local_min > threshold )") ] )
        headerList.append( ["price change deviation:", ("price_change.stddev * len( price_change )") ] )
        headerList.append( [] )

        retDataFrame: pandas.DataFrame = overall_stats.generateDataFrame( namesSet )

        write_to_csv( file, headerList, retDataFrame )

        _LOGGER.debug( "Done" )

        return retDataFrame

    def calculateActivityForDay( self, day_stock_list, stats_dict: StatsDict, thresholdPercent, result_stats: StatsDict ):
        for dataFrame in day_stock_list:
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

            dataSubdict    = result_stats[ name ]
            precalcSubdict = stats_dict[ name ]

            minValue = precalcSubdict["min price"]
            dataSubdict.minValue( "min price", minValue )                                  ## min value

            maxValue = precalcSubdict["max price"]
            dataSubdict.maxValue( "max price", maxValue )                                  ## max value

            dataSubdict["ref price"] = precalcSubdict["ref price"]

            calcRet = precalcSubdict["trading [kPLN]"]
            dataSubdict.add( "trading [kPLN]", calcRet )                                   ## trading

            dataSubdict[ "trading/day [kPLN]" ] = 0.0                     ## placeholder for further calc

            dataSubdict["potential"]   = precalcSubdict["potential"]
            dataSubdict["relative"]    = precalcSubdict["relative"]
            dataSubdict["pot raise %"] = precalcSubdict["pot raise %"]

            calcRet = VarCalc.calcChange3(priceColumn, thresholdPercent)
            dataSubdict.add( "price activity", calcRet[1] )                           ## price activity

            calcRet = precalcSubdict["price change sum"]
            dataSubdict.add( "price change sum", calcRet )                            ## price change sum

            calcRet = precalcSubdict["price change deviation"]
            dataSubdict.add( "price change deviation", calcRet )                      ## price change deviation

    ### returns ( dataframe_list, stats_dict, date )
    def getPrecalcData(self, currDate):
#         _LOGGER.debug( "loading data for: %s", currDate )

        date_year  = currDate.year
        dateString = currDate.isoformat()
        picklePath = f"{TMP_DIR}data/activity/{date_year}/{dateString}.pickle"

        dataPair = None
        if self.forceRecalc is False:
            dataPair = persist.load_object_simple( picklePath, None, silent=True )

        if dataPair is None or len(dataPair[0]) < 1:
            ## happens in two cases: loaded cache data is invalid or self.forceRecalc is True
#                 _LOGGER.debug( "no precalculated data found -- precalculating [%s]", picklePath )
            dataPair = self.precalculateData( currDate )
            persist.store_object_simple(dataPair, picklePath)

        return list( dataPair ) + [ currDate ]

    ## returns: ( List[DataFrame], Dict )
    def precalculateData(self, currDate):
        day_stock_list = self._loadData( currDate )

        stats_dict = StatsDict()

        for dataFrame in day_stock_list:
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

            dataSubdict = stats_dict[ name ]

            minValue = priceColumn.min()
            if math.isnan( minValue ) is False:
                dataSubdict["min price"] = minValue                              ## min value

            maxValue = priceColumn.max()
            if math.isnan( maxValue ) is False:
                dataSubdict["max price"] = maxValue                              ## max value

            dataSubdict["ref price"] = priceColumn.iloc[ priceSize - 1 ]         ## get last value

            volumenColumn = dataFrame["volumen"]
            tradingColumn = priceColumn * volumenColumn / 1000
            calcRet = VarCalc.calcSum( tradingColumn )
            dataSubdict["trading [kPLN]"] = calcRet                              ## trading

            dataSubdict["potential"]   = 0.0
            dataSubdict["relative"]    = 0.0
            dataSubdict["pot raise %"] = 0.0

            priceChangeColumn = calculate_change( priceColumn )
            calcRet = priceChangeColumn.sum()
            dataSubdict["price change sum"] = calcRet                            ## price change sum

            calcRet = priceChangeColumn.std() * len( priceColumn )
            if math.isnan( calcRet ):
                calcRet = 0.0
            dataSubdict["price change deviation"] = calcRet                      ## price change deviation

        return ( day_stock_list, stats_dict )

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
