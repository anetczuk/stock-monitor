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
from stockdataaccess.dataaccess.worksheetdata import WorksheetData, BaseWorksheetDAO
from stockdataaccess.dataaccess import download_html_content
from stockdataaccess.synchronized import synchronized
from stockdataaccess.dataaccess.datatype import StockDataType
from stockdataaccess.pprint import fullname


_LOGGER = logging.getLogger(__name__)


class FinRepsCalendarData( BaseWorksheetDAO ):

    class DAO( WorksheetData ):
        """Data access object."""

        def getDataPath(self):
            return TMP_DIR + "data/strefa/fin_reps_cal_data.html"

        ## override
        def downloadData(self, filePath):
            url = ("https://strefainwestorow.pl/dane/raporty/lista-dat-publikacji-raportow-okresowych/wszystkie"
                   "?sort=asc&order=Data%20publikacji" )

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
            dataFrame = pandas.read_html( dataFile )
            dataFrame = dataFrame[0]
            return dataFrame

    ## ==========================================================

    def __init__(self):
        dao = FinRepsCalendarData.DAO()
        super().__init__( dao )

    def sourceLink(self):
        return "https://strefainwestorow.pl/dane/raporty/lista-dat-publikacji-raportow-okresowych/wszystkie"

    def getTicker(self, rowIndex):
        return self.getDataByIndex( StockDataType.TICKER, rowIndex )

    ## get column index
    ## override
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
        switcher = {
            StockDataType.TICKER: 1
        }
        colIndex = switcher.get(columnType, None)
        if colIndex is None:
            raise ValueError( f"Invalid value: {columnType}" )
        return colIndex


class PublishedFinRepsCalendarData( BaseWorksheetDAO ):

    class DAO( WorksheetData ):
        """Data access object."""

        def getDataPath(self):
            return TMP_DIR + "data/strefa/fin_reps_cal_publ_data.html"

        ## override
        def downloadData(self, filePath):
            url = ("https://strefainwestorow.pl/dane/raporty/lista-dat-publikacji-raportow-okresowych/opublikowane"
                   "?sort=desc&order=Data%20publikacji" )

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
            dataFrame = pandas.read_html( dataFile )
            dataFrame = dataFrame[0]
            dataFrame['Ticker'] = dataFrame['Ticker'].str.replace( '#', '' )
            return dataFrame

    ## ==========================================================

    def __init__(self):
        dao = PublishedFinRepsCalendarData.DAO()
        super().__init__( dao )

    def sourceLink(self):
        return "https://strefainwestorow.pl/dane/raporty/lista-dat-publikacji-raportow-okresowych/opublikowane"

    def getTicker(self, rowIndex):
        return self.getDataByIndex( StockDataType.TICKER, rowIndex )

    ## get column index
    ## override
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
        switcher = {
            StockDataType.TICKER: 1
        }
        colIndex = switcher.get(columnType, None)
        if colIndex is None:
            raise ValueError( f"Invalid value: {columnType}" )
        return colIndex
