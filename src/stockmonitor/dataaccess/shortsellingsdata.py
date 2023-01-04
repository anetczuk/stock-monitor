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

from bs4 import BeautifulSoup

from stockdataaccess.synchronized import synchronized
from stockdataaccess.pprint import fullname
from stockmonitor.dataaccess import tmp_dir, requests_init_session
from stockmonitor.dataaccess.worksheetdata import WorksheetData, BaseWorksheetDAO
from stockmonitor.dataaccess.datatype import StockDataType


_LOGGER = logging.getLogger(__name__)


def grab_content( url, button ):
    with requests_init_session() as currSession:
        resp = currSession.get( url )
        resp.raise_for_status()
        content = resp.content

        soup = BeautifulSoup( content, "html.parser" )

# POST /RssOuterView/faces/start2OuterView.xhtml HTTP/1.1
# Host: rss.knf.gov.pl
# User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0
# Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
# Accept-Language: en-US,en;q=0.5
# Accept-Encoding: gzip, deflate, br
# Content-Type: application/x-www-form-urlencoded
# Content-Length: 174
# Origin: https://rss.knf.gov.pl
# Connection: keep-alive
# Referer: https://rss.knf.gov.pl/RssOuterView/faces/start2OuterView.xhtml
# Cookie: JSESSIONID=592cd6515489808fc6441df4fcb8; __utmc=209674056; cookiesession1=61A38EB6ATSUTV1491ISM9V9A7H0D358
# Upgrade-Insecure-Requests: 1
# Sec-Fetch-Dest: document
# Sec-Fetch-Mode: navigate
# Sec-Fetch-Site: same-origin
# Sec-Fetch-User: ?1

# j_idt8=j_idt8
# j_idt8-j_idt14=Lista pozycji aktualnych
# tokenv=N0MMSW708JZG602RFTNFYJF700RU3VS0EGB669MAYB5SNC8V
# javax.faces.ViewState=9187231122682369284:-2736673537589052604

        postUrl = "https://rss.knf.gov.pl/RssOuterView/faces/start2OuterView.xhtml"
        postData = {}
        postData["j_idt8"]                = soup.find( 'input', {'name': 'j_idt8'} ).get('value')
        postData[ button ]                = soup.find( 'input', {'name': button} ).get('value')
        postData["tokenv"]                = soup.find( 'input', {'name': 'tokenv'} ).get('value')
        postData["javax.faces.ViewState"] = soup.find( 'input', {'name': 'javax.faces.ViewState'} ).get('value')

#         _LOGGER.debug( "content:\n%s", soup )
#         _LOGGER.debug( "POST data: %s\n%s", postUrl, postData )

        resp = currSession.post( postUrl, data=postData )
#         req = requests.Request('POST', postUrl, data=postData )
#         prepped = req.prepare()
#
#         resp = currSession.send( prepped )
        resp.raise_for_status()

        strcontent = resp.content.decode( "utf-8" )
        return strcontent

    ## old version
#         session = dryscrape.Session()
#         session.visit( url )
#         loadButton = session.at_xpath('//*[@name="j_idt8-j_idt14"]')        ## aktualne
#         loadButton.click()
#         return session.body()


## https://rss.knf.gov.pl/RssOuterView/
class CurrentShortSellingsData( BaseWorksheetDAO ):

    class DAO( WorksheetData ):
        """Data access object."""

        ## override
        def getDataPath(self):
            return tmp_dir + "data/knf/shortsellings-current.html"

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
                response = grab_content( url, "j_idt8-j_idt14" )
                with open( filePath, "w", encoding="utf-8" ) as text_file:
                    text_file.write( response )
            except BaseException as ex:
                _LOGGER.exception( "unable to load object data -- %s: %s", fullname(ex), ex, exc_info=False )
                raise

        ## override
        @synchronized
        def _parseDataFromFile(self, dataFile) -> DataFrame:
#             _LOGGER.debug( "parsing data file: %s", dataFile )
            dataFrame = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
            #_LOGGER.debug( "dataFrame: %s", dataFrame )
            if len(dataFrame) < 3:
                _LOGGER.warning( "unable to parse data file: %s", dataFile )
                return None
            dataFrame = dataFrame[3]

    #         print( "raw dataframe:\n", dataFrame )
            dataFrame.drop( dataFrame.columns[0], axis=1, inplace=True )        ## remove first column
            dataFrame.drop( dataFrame.tail(1).index, inplace=True )             ## remove last row (navigation bar)

            dataFrame = dataFrame.fillna("-")
            return dataFrame

    ## ==========================================================

    def __init__(self):
        dao = CurrentShortSellingsData.DAO()
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
class HistoryShortSellingsData( BaseWorksheetDAO ):

    class DAO( WorksheetData ):
        """Data access object."""

        ## override
        def getDataPath(self):
            return tmp_dir + "data/knf/shortsellings-history.html"

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
                response = grab_content( url, "j_idt8-j_idt16" )
                with open( filePath, "w", encoding="utf-8" ) as text_file:
                    text_file.write( response )
            except BaseException as ex:
                _LOGGER.exception( "unable to load object data -- %s: %s", fullname(ex), ex, exc_info=False )
                raise

        ## override
        def _parseDataFromFile(self, dataFile) -> DataFrame:
#             _LOGGER.debug( "parsing data file: %s", dataFile )
            dataFrame = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
            if len( dataFrame ) < 3:
                _LOGGER.warning( "received unexpected data while parsing: %s", dataFile )
                return None
            dataFrame = dataFrame[3]

            dataFrame.drop( dataFrame.columns[0], axis=1, inplace=True )        ## remove first column
            dataFrame.drop( dataFrame.tail(1).index, inplace=True )             ## remove last row (navigation bar)

            dataFrame = dataFrame.fillna("-")
            return dataFrame

    ## ==========================================================

    def __init__(self):
        dao = HistoryShortSellingsData.DAO()
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
