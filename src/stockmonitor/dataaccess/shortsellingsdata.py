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

import logging
import pandas
from pandas.core.frame import DataFrame

import requests
from bs4 import BeautifulSoup
# import dryscrape

from stockmonitor.dataaccess import tmp_dir
from stockmonitor.dataaccess.worksheetdata import WorksheetData


_LOGGER = logging.getLogger(__name__)


def grab_content( url, button ):
    with requests.Session() as currSession:
        currSession.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
        content = currSession.get( url ).content
        soup = BeautifulSoup( content, "html.parser" )
#             print( "aaaaa\n", soup )

        postUrl = "https://rss.knf.gov.pl/RssOuterView/faces/start2OuterView.xhtml"
        postData = {}
        postData["j_idt8"]                = soup.find( 'input', {'name': 'j_idt8'} ).get('value')
        postData[ button ]                = soup.find( 'input', {'name': button} ).get('value')
        postData["tokenv"]                = soup.find( 'input', {'name': 'tokenv'} ).get('value')
        postData["javax.faces.ViewState"] = soup.find( 'input', {'name': 'javax.faces.ViewState'} ).get('value')

        req = requests.Request('POST', postUrl, data=postData )
        prepped = req.prepare()

        resp = currSession.send( prepped )
        soup = BeautifulSoup( resp.content, "html.parser" )
#             print( soup )
        return soup

    ## old version
#         session = dryscrape.Session()
#         session.visit( url )
#         loadButton = session.at_xpath('//*[@name="j_idt8-j_idt14"]')        ## aktualne
#         loadButton.click()
#         return session.body()


## https://rss.knf.gov.pl/RssOuterView/
class CurrentShortSellingsData( WorksheetData ):

    ## override
    def parseDataFromFile(self, dataFile) -> DataFrame:
        _LOGGER.debug( "parsing data file: %s", dataFile )
        dataFrame = pandas.read_html( dataFile, thousands='', decimal=',' )
        dataFrame = dataFrame[3]
        dataFrame = dataFrame.fillna("-")
        return dataFrame

    ## override
    def _downloadContent( self, url, filePath ):
        response = self._grabContent( url )
        with open( filePath, "w" ) as text_file:
            text_file.write( response )

    def _grabContent( self, url ):
        return grab_content( url, "j_idt8-j_idt14" )

    ## override
    def getDataPath(self):
        return tmp_dir + "data/knf/shortsellings-current.html"

    ## override
    def getDataUrl(self):
        url = "https://rss.knf.gov.pl/RssOuterView/"
        return url

    ## override
    def sourceLink(self):
        return self.getDataUrl()


## https://rss.knf.gov.pl/RssOuterView/
class HistoryShortSellingsData( WorksheetData ):

    ## override
    def parseDataFromFile(self, dataFile) -> DataFrame:
        _LOGGER.debug( "parsing data file: %s", dataFile )
        dataFrame = pandas.read_html( dataFile, thousands='', decimal=',' )
        dataFrame = dataFrame[3]
        dataFrame = dataFrame.fillna("-")
        return dataFrame

    ## override
    def _downloadContent( self, url, filePath ):
        response = self._grabContent( url )
        with open( filePath, "w" ) as text_file:
            text_file.write( response )

    def _grabContent( self, url ):
        return grab_content( url, "j_idt8-j_idt16" )

    ## override
    def getDataPath(self):
        return tmp_dir + "data/knf/shortsellings-history.html"

    ## override
    def getDataUrl(self):
        url = "https://rss.knf.gov.pl/RssOuterView/"
        return url

    ## override
    def sourceLink(self):
        return self.getDataUrl()
