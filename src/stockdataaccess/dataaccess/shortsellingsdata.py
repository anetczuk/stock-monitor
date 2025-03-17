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
import json
from pandas.core.frame import DataFrame

from stockdataaccess.dataaccess import TMP_DIR, requests_init_session
from stockdataaccess.dataaccess.worksheetdata import WorksheetDAO, BaseWorksheetData
from stockdataaccess.synchronized import synchronized
from stockdataaccess.dataaccess.datatype import StockDataType
from stockdataaccess.pprint import fullname


_LOGGER = logging.getLogger(__name__)


def grab_shorts_current():
    return grab_shorts_data("Default")


def grab_shorts_hist():
    return grab_shorts_data("RssHTable")


def grab_shorts_data(method):
    with requests_init_session() as currSession:

        postUrl = "https://rss.knf.gov.pl/rss_pub/JSON"

        headers = { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' }

        postData = {
            "cmd": "get",
            "language": "pl",
            "search": [],
            "limit": 200,
            "offset": 0,
            "method": method,
            "sort": [
                {
                    "field": "POSITION_DATE",
                    "direction": "desc"
                }
            ],
            "searchLogic": "AND",
            "searchValue": ""
        }

        raw_data = { 'request': json.dumps(postData) }

        resp = currSession.post( postUrl, headers=headers, data=raw_data )
        resp.raise_for_status()

        strcontent = resp.content.decode( "utf-8" )
        return strcontent


## https://rss.knf.gov.pl/RssOuterView/
class CurrentShortSellingsData( BaseWorksheetData ):

    class CurrentShortSellingsDAO( WorksheetDAO ):
        """Data access object."""

        ## override
        def getDataPath(self):
            return TMP_DIR + "data/knf/shortsellings-current.json"

        ## override
        def getDataUrl(self):
            url = "https://rss.knf.gov.pl/RssOuterView/"
            return url

        ## override
        def downloadData(self, filePath):
            url = self.getDataUrl()

            relPath = os.path.relpath( filePath )
            _LOGGER.debug( "grabbing data from url[%s] as file[%s]", url.split("?", maxsplit=1)[0], relPath )

            try:
                response = grab_shorts_current()
                with open( filePath, "w", encoding="utf-8" ) as text_file:
                    text_file.write( response )
            except BaseException as ex:
                _LOGGER.exception( "unable to load object data -- %s: %s", fullname(ex), ex, exc_info=False )
                raise

        ## override
        @synchronized
        def _parseDataFromFile(self, dataFile) -> DataFrame:
#             _LOGGER.debug( "parsing data file: %s", dataFile )
            with open( dataFile, "r", encoding="utf-8" ) as json_file:
                json_data = json.load(json_file)

            records = json_data["records"]
            dataFrame = DataFrame.from_records(records)

    #         dataFrame = dataFrame.fillna("-")
            dataFrame.drop( "recid", axis=1, inplace=True )             ## remove column
            return dataFrame

    ## ==========================================================

    def __init__(self):
        dao = CurrentShortSellingsData.CurrentShortSellingsDAO()
        super().__init__( dao )

    ## override
    def sourceLink(self):
        return self.dao.getDataUrl()

    def getISIN(self, rowIndex):
        return self.getDataByIndex( StockDataType.ISIN, rowIndex )

    ## get column index
    ## override
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
        switcher = {
            StockDataType.ISIN: 2
        }
        colIndex = switcher.get(columnType, None)
        if colIndex is None:
            raise ValueError( f"Invalid value: {columnType}" )
        return colIndex


## ================================================================


## https://rss.knf.gov.pl/RssOuterView/
class HistoryShortSellingsData( BaseWorksheetData ):

    class HistoryShortSellingsDAO( WorksheetDAO ):
        """Data access object."""

        ## override
        def getDataPath(self):
            return TMP_DIR + "data/knf/shortsellings-history.html"

        ## override
        def getDataUrl(self):
            url = "https://rss.knf.gov.pl/rss_pub/rssH.html"
            return url

        ## override
        def downloadData(self, filePath):
            url = self.getDataUrl()

            relPath = os.path.relpath( filePath )
            _LOGGER.debug( "grabbing data from url[%s] as file[%s]", url.split("?", maxsplit=1)[0], relPath )

            try:
                response = grab_shorts_hist()
                with open( filePath, "w", encoding="utf-8" ) as text_file:
                    text_file.write( response )
            except BaseException as ex:
                _LOGGER.exception( "unable to load object data -- %s: %s", fullname(ex), ex, exc_info=False )
                raise

        ## override
        def _parseDataFromFile(self, dataFile) -> DataFrame:
#             _LOGGER.debug( "parsing data file: %s", dataFile )
            with open( dataFile, "r", encoding="utf-8" ) as json_file:
                json_data = json.load(json_file)

            records = json_data["records"]
            dataFrame = DataFrame.from_records(records)

    #         dataFrame = dataFrame.fillna("-")
            dataFrame.drop( "recid", axis=1, inplace=True )             ## remove column
            return dataFrame

    ## ==========================================================

    def __init__(self):
        dao = HistoryShortSellingsData.HistoryShortSellingsDAO()
        super().__init__( dao )

    ## override
    def sourceLink(self):
        return self.dao.getDataUrl()

    def getISIN(self, rowIndex):
        return self.getDataByIndex( StockDataType.ISIN, rowIndex )

    ## get column index
    ## override
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
        switcher = {
            StockDataType.ISIN: 2
        }
        colIndex = switcher.get(columnType, None)
        if colIndex is None:
            raise ValueError( f"Invalid value: {columnType}" )
        return colIndex
