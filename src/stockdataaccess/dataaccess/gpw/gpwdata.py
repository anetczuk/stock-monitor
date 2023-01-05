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

import pandas
from pandas.core.frame import DataFrame

from stockdataaccess.dataaccess import TMP_DIR
from stockdataaccess.dataaccess.datatype import StockDataType
from stockdataaccess.dataaccess.convert import convert_float, convert_int, cleanup_column, apply_on_column
from stockdataaccess.dataaccess.worksheetdata import WorksheetDAO, BaseWorksheetData
from stockdataaccess.dataaccess import download_html_content
from stockdataaccess.synchronized import synchronized
from stockdataaccess.pprint import fullname


_LOGGER = logging.getLogger(__name__)


## https://www.gpw.pl/wskazniki
class GpwIndicatorsData( BaseWorksheetData ):

    class GpwIndicatorsDAO( WorksheetDAO ):
        """Data access object."""

        def getDataPath(self):
            return TMP_DIR + "data/gpw/indicators_data.html"

        def getDataUrl(self):
            return "https://www.gpw.pl/wskazniki"

        ## override
        def downloadData(self, filePath):
            url = self.getDataUrl()
            url_short = url.split("?", maxsplit=1)[0]

            relPath = os.path.relpath( filePath )
            _LOGGER.debug( "grabbing data from url[%s] as file[%s]", url_short, relPath )

            try:
                download_html_content( url, filePath )
            except BaseException as ex:
                _LOGGER.exception( "unable to load object data from %s -- %s: %s",
                                   url_short, fullname(ex), ex, exc_info=False )
                raise

        @synchronized
        def _parseDataFromFile(self, dataFile: str) -> DataFrame:
#             _LOGGER.debug( "opening workbook: %s", dataFile )
            allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
            dataFrame = DataFrame()
            dataFrame = dataFrame.append( allDataFrames[1] )            ## country
            dataFrame = dataFrame.append( allDataFrames[2] )            ## foreign

            cleanup_column( dataFrame, 'Sektor' )

            apply_on_column( dataFrame, 'Liczba wyemitowanych akcji', convert_int )
            apply_on_column( dataFrame, 'Wartość rynkowa (mln zł)', convert_float )
            apply_on_column( dataFrame, 'Wartość księgowa (mln zł)', convert_float )

            apply_on_column( dataFrame, 'C/WK', convert_float )
            apply_on_column( dataFrame, 'C/Z', convert_float )
            apply_on_column( dataFrame, 'Stopa dywidendy (%)', convert_float )

            return dataFrame

    def __init__(self):
        dao = GpwIndicatorsData.GpwIndicatorsDAO()
        super().__init__( dao )

    def sourceLink(self):
        return self.dao.getDataUrl()

    def getStockIsin(self, rowIndex):
        return self.getDataByIndex( StockDataType.ISIN, rowIndex)

    ## get column index
    ## override
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
        switcher = {
            StockDataType.ISIN: 1
        }
        colIndex = switcher.get(columnType, None)
        if colIndex is None:
            raise ValueError( f"Invalid value: {columnType}" )
        return colIndex


## ==========================================================================


## http://infostrefa.com/infostrefa/pl/spolki
class GpwIsinMapData( BaseWorksheetData ):

    class GpwIsinMapDAO( WorksheetDAO ):
        """Data access object."""

        def getDataPath(self):
            return TMP_DIR + "data/gpw/isin_map_data.html"

            ## override
        def downloadData(self, filePath):
            ## this source does not seem to be viable,
            ## because it lacks a lot of tickers/isin values
            url = "http://infostrefa.com/infostrefa/pl/spolki"

            relPath = os.path.relpath( filePath )
            _LOGGER.debug( "grabbing data from url[%s] as file[%s]", url.split("?", maxsplit=1)[0], relPath )

            try:
                download_html_content( url, filePath )
            except BaseException as ex:
                _LOGGER.exception( "unable to load object data -- %s: %s", fullname(ex), ex, exc_info=False )
                raise

        @synchronized
        def _parseDataFromFile(self, dataFile: str) -> DataFrame:
#             _LOGGER.debug( "opening workbook: %s", dataFile )
            allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
            dataFrame = allDataFrames[1]
            return dataFrame

    ## ==========================================================

    def __init__(self):
        dao = GpwIsinMapData.GpwIsinMapDAO()
        super().__init__( dao )

    def getTickerFromIsin(self, stockIsin):
        return self.getDataByValue( StockDataType.ISIN, stockIsin, StockDataType.TICKER )

    def getTickerFromName(self, stockName):
        return self.getDataByValue( StockDataType.STOCK_NAME, stockName, StockDataType.TICKER )

    def getStockIsinFromTicker(self, ticker):
        return self.getDataByValue( StockDataType.TICKER, ticker, StockDataType.ISIN )

    def getNameFromTicker(self, ticker):
        return self.getDataByValue( StockDataType.TICKER, ticker, StockDataType.FULL_NAME )

    ## get column index
    ## override
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
        switcher = {
            StockDataType.FULL_NAME:  0,
            StockDataType.STOCK_NAME: 1,
            StockDataType.TICKER:     2,
            StockDataType.ISIN:       3
        }
        colIndex = switcher.get(columnType, None)
        if colIndex is None:
            raise ValueError( f"Invalid value: {columnType}" )
        return colIndex
