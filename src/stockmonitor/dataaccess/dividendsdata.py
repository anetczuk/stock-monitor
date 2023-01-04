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
import pandas
from pandas.core.frame import DataFrame

from stockdataaccess.synchronized import synchronized
from stockdataaccess.pprint import fullname
from stockmonitor.dataaccess import tmp_dir
from stockmonitor.dataaccess.worksheetdata import WorksheetData, BaseWorksheetDAO
from stockmonitor.dataaccess import download_html_content
from stockmonitor.dataaccess.datatype import StockDataType


_LOGGER = logging.getLogger(__name__)


## https://www.stockwatch.pl/dywidendy/
class DividendsCalendarData( BaseWorksheetDAO ):

    class DividendsCalendarDAO( WorksheetData ):
        """Data access object."""

        def getDataPath(self):
            return tmp_dir + "data/stockwatch/dividends_cal_data.html"

        def getDataUrl(self):
            url = "https://www.stockwatch.pl/dywidendy/"
            return url

        ## override
        def downloadData(self, filePath):
            url = self.getDataUrl()

            relPath = os.path.relpath( filePath )
            _LOGGER.debug( "grabbing data from url[%s] as file[%s]", url.split("?", maxsplit=1)[0], relPath )

            try:
                download_html_content( url, filePath )
            except BaseException as ex:
                _LOGGER.exception( "unable to load object data -- %s: %s", fullname(ex), ex, exc_info=False )
                raise

        @synchronized
        def _parseDataFromFile(self, dataFile) -> DataFrame:
            ## _LOGGER.debug( "opening workbook: %s", dataFile )

            with open( dataFile, encoding="utf-8" ) as file:
                content = file.read()
                if "Brak informacji o dywidendach" in content:
                    ## no data found
                    return None

            dataFrame = pandas.read_html( dataFile, thousands='', decimal=',' )
            dataFrame = dataFrame[2]
            dataFrame = dataFrame.fillna("-")
            return dataFrame

    ## ==========================================================

    def __init__(self):
        dao = DividendsCalendarData.DividendsCalendarDAO()
        super().__init__( dao )

    def sourceLink(self):
        return self.dao.getDataUrl()

    def getStockName(self, rowIndex):
        return self.getDataByIndex( StockDataType.STOCK_NAME, rowIndex)

    def getLawDate(self, rowIndex):
        dateString = self.getDataByIndex( StockDataType.NO_DIV_DAY, rowIndex)
        try:
            dateObject = datetime.datetime.strptime(dateString, '%Y-%m-%d').date()
            return dateObject
        except ValueError:
            return datetime.date( 1, 1, 1 )

    ## get column index
    ## override
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
        switcher = {
            StockDataType.STOCK_NAME: 0,
            StockDataType.NO_DIV_DAY: 5
        }
        colIndex = switcher.get(columnType, None)
        if colIndex is None:
            raise ValueError( f"Invalid value: {columnType}" )
        return colIndex
