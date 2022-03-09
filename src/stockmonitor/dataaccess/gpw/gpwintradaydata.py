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

import json
from pandas.core.frame import DataFrame

from stockmonitor.dataaccess import tmp_dir
from stockmonitor.dataaccess.worksheetdata import WorksheetData, BaseWorksheetDAO
from stockmonitor.dataaccess import download_html_content
from stockmonitor.dataaccess.convert import apply_on_column, convert_timestamp_datetime
from stockmonitor.synchronized import synchronized
from stockmonitor.pprint import fullname
from stockmonitor.dataaccess.datatype import StockDataType


_LOGGER = logging.getLogger(__name__)


class GpwCurrentStockIntradayData( BaseWorksheetDAO ):
    """Handle GPW 1D data chart."""

    class DAO( WorksheetData ):
        """Data access object."""

        def __init__(self, isin, rangeCode=None):
            super().__init__()
            if rangeCode is None:
                rangeCode = "1D"
            self.isin      = isin
            self.rangeCode = rangeCode
            self.dataTime  = datetime.datetime.now()

        def getDataPath(self):
            modeCode = mode_code( self.rangeCode )
            currDate = self.dataTime.date()
            dateStr  = str(currDate)
            return f"{tmp_dir}data/gpw/curr/{dateStr}/isin_{self.isin}_{modeCode}.json"

        ## override
        def downloadData(self, filePath):
            modeCode = mode_code( self.rangeCode )
    #         currTimestamp = self.dataTime.timestamp()
            url = generate_chart_data_url( self.isin, modeCode)

            relPath = os.path.relpath( filePath )
            _LOGGER.debug( "grabbing data from url[%s] as file[%s]", url, relPath )
#             _LOGGER.debug( "grabbing data from url[%s] as file[%s]", url.split("?", maxsplit=1)[0], relPath )

            try:
                download_html_content( url, filePath )
            except BaseException as ex:
                _LOGGER.exception( "unable to load object data -- %s: %s", fullname(ex), ex, exc_info=False )
                raise

        @synchronized
        def getWorksheetForDate(self, dataDate, forceRefresh=False):
            self.dataTime = datetime.datetime.combine( dataDate, datetime.time.max )
            return self.getWorksheetData( forceRefresh )

        def loadWorksheet(self):
            self.dataTime = datetime.datetime.now()
            super().loadWorksheet()

        @synchronized
        def _parseDataFromFile(self, dataFile: str) -> DataFrame:
            with open( dataFile, encoding="utf-8" ) as f:
                json_data = json.load(f)
                json_dict = json_data[0]
                data_field = json_dict.get("data", None)
                if data_field is None:
                    _LOGGER.warning("no 'data' field found")
                    return None
    #             print("xxx:", data_field)

                ## example data
                #            c      h      l      o      p           t      v
                # 0     418.4  419.8  418.4  419.8  418.4  1599202800  11141
                # 1     419.0  419.0  418.1  418.4  419.0  1599202801    334
                # 2     418.0  419.5  418.0  419.0  418.0  1599202802    130

                dataFrame = DataFrame( data_field )
    #             print( "xxx:\n", dataFrame )

                apply_on_column( dataFrame, 't', convert_timestamp_datetime )

                if self.rangeCode != "1D":
                    ## add recent value to range other than "1D" (current)
                    currData = GpwCurrentStockIntradayData.DAO( self.isin )
                    currData.dataTime = self.dataTime
                    currWorksheet = currData.getWorksheetData()
                    if currWorksheet is not None:
                        lastRow = currWorksheet.iloc[-1]
                        dataFrame = dataFrame.append( lastRow )
                        dataFrame.reset_index( drop=True, inplace=True )

                return dataFrame

            return None

    ## ==========================================================

    def __init__(self, isin, rangeCode=None):
        dao = GpwCurrentStockIntradayData.DAO( isin, rangeCode )
        super().__init__( dao )

    def sourceLink(self):
        return "https://www.gpw.pl/spolka?isin=" + self.dao.isin

    def getWorksheetForDate(self, dataDate, forceRefresh=False):
        return self.dao.getWorksheetForDate( dataDate, forceRefresh )

    ## get column index
    ## override
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
        raise ValueError( f"Invalid value: {columnType}" )


class GpwCurrentIndexIntradayData( BaseWorksheetDAO ):

    class DAO( WorksheetData ):
        """Data access object."""

        def __init__(self, isin, rangeCode=None):
            super().__init__()
            if rangeCode is None:
                rangeCode = "1D"
            self.isin      = isin
            self.rangeCode = rangeCode
            self.dataTime  = datetime.datetime.now()

        def getDataPath(self):
            modeCode = mode_code( self.rangeCode )
            currDate = self.dataTime.date()
            dateStr  = str(currDate)
            return f"{tmp_dir}data/gpw/curr/{dateStr}/isin_{self.isin}_{modeCode}.json"

        ## override
        def downloadData(self, filePath):
            modeCode      = mode_code( self.rangeCode )
    #         currTimestamp = self.dataTime.timestamp()
            url = generate_chart_data_url( self.isin, modeCode)

            relPath = os.path.relpath( filePath )
            _LOGGER.debug( "grabbing data from url[%s] as file[%s]", url.split("?", maxsplit=1)[0], relPath )

            try:
                download_html_content( url, filePath )
            except BaseException as ex:
                _LOGGER.exception( "unable to load object data -- %s: %s", fullname(ex), ex, exc_info=False )
                raise

        def loadWorksheet(self):
            self.dataTime = datetime.datetime.now()
            super().loadWorksheet()

        @synchronized
        def _parseDataFromFile(self, dataFile: str) -> DataFrame:
            with open( dataFile, encoding="utf-8" ) as f:
                json_data = json.load(f)
                json_dict = json_data[0]
                data_field = json_dict.get("data", None)
                if data_field is None:
                    return None
    #             print("xxx:", data_field)

                ## example data
                #              c        h        l        o        p           t
                # 0     1765.37  1765.37  1765.37  1765.37  1765.37  1599462009
                # 1     1768.42  1768.42  1768.42  1768.42  1768.42  1599462015
                # 2     1768.49  1768.49  1768.49  1768.49  1768.49  1599462030

                dataFrame = DataFrame( data_field )
    #             print( "xxx:\n", dataFrame )

                apply_on_column( dataFrame, 't', convert_timestamp_datetime )

                return dataFrame

            return None

    def __init__(self, isin, rangeCode=None):
        dao = GpwCurrentIndexIntradayData.DAO( isin, rangeCode )
        super().__init__( dao )

    def sourceLink(self):
        return "https://gpwbenchmark.pl/karta-indeksu?isin=" + self.dao.isin

    ## get column index
    ## override
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
        raise ValueError( f"Invalid value: {columnType}" )


## ================================================================


def mode_code( modeText ):
    modeCode = modeText
    if modeCode == "1D":
        modeCode = "CURR"
    elif modeCode == "MAX":
        modeCode = "ARCH"
    return modeCode


def generate_chart_data_mode_url(isin, modeCode):
    return "https://www.gpw.pl/chart-json.php?req=[{%22isin%22:%22" + isin + "%22" + \
           ",%22mode%22:%22" + modeCode + "%22}]"


## fields 'from' and 'to' are useful in 'RANGE' mode (returned data
## is in day resolution)
def generate_chart_data_range_url( isin, timeRange: datetime.timedelta ):
    modeCode = "RANGE"

    todayDateTime = datetime.datetime.now()
    todayString = todayDateTime.strftime("%Y-%m-%d")

    startDateTime = todayDateTime - timeRange
    startString   = startDateTime.strftime("%Y-%m-%d")

    return "https://www.gpw.pl/chart-json.php?req=[{%22isin%22:%22" + isin + "%22" + \
           ",%22mode%22:%22" + modeCode + "%22,%22from%22:%22" + startString + \
           "%22,%22to%22:%22" + todayString + "%22}]"


def generate_chart_data_url(isin, modeCode):
    ## valid modes: CURR, 14D, 1M, 3M, 6M, 1R, ARCH
    if modeCode == "CURR":
        return generate_chart_data_mode_url( isin, modeCode )
    if modeCode == "14D":
        return generate_chart_data_mode_url( isin, modeCode )
    if modeCode == "1M":
        return generate_chart_data_mode_url( isin, modeCode )
    if modeCode == "3M":
        return generate_chart_data_mode_url( isin, modeCode )
    if modeCode == "6M":
        return generate_chart_data_mode_url( isin, modeCode )
    if modeCode == "1R":
        return generate_chart_data_mode_url( isin, modeCode )
    if modeCode == "ARCH":
        return generate_chart_data_mode_url( isin, modeCode )

    if modeCode == "2R":
        timeRange = datetime.timedelta( weeks=104 )
        return generate_chart_data_range_url( isin, timeRange )
    if modeCode == "3R":
        timeRange = datetime.timedelta( weeks=156 )
        return generate_chart_data_range_url( isin, timeRange )

    ## else -- use mode
    _LOGGER.warning( "unknown mode: %s", modeCode )
    return generate_chart_data_mode_url( isin, modeCode )
