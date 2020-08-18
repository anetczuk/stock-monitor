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
import urllib

import pandas
from pandas.core.frame import DataFrame

from stockmonitor import persist
from stockmonitor.dataaccess import tmp_dir


_LOGGER = logging.getLogger(__name__)


## https://info.bossa.pl/index.jsp?layout=intraday&page=1&news_cat_id=875&dirpath=/mstock/daily/
class MetaStockIntradayData:

    def __init__(self):
        self.worksheet: DataFrame = None
        self.grabTimestamp: datetime.datetime = None

    def refreshData(self):
        self.loadWorksheet( True )

    def getWorksheet(self, forceRefresh=False) -> DataFrame:
        if self.worksheet is None or forceRefresh is True:
            self.loadWorksheet( forceRefresh )
        return self.worksheet

    def loadWorksheet(self, forceRefresh=False):
        dataFile, timestampFile = self.getDataFile( forceRefresh )
        self.worksheet = self.getWorksheetFromFile( dataFile )
        if timestampFile is not None:
            self.grabTimestamp = persist.load_object_simple( timestampFile, None )
        else:
            self.grabTimestamp = None

    def getDataFile(self, forceRefresh=False):
        filePath      = tmp_dir + "data/bossa/recent_intraday_data.prn"
        timestampPath = tmp_dir + "data/bossa/recent_intraday_timestamp.txt"
        if forceRefresh is False and os.path.exists( filePath ):
            _LOGGER.debug( "loading recent data from file[%s]", filePath )
            return (filePath, timestampPath)

        url = "https://info.bossa.pl/pub/intraday/mstock/daily//a_cgl.prn"
        _LOGGER.debug( "grabbing data from url[%s] to file[%s]", url, filePath )

        currTimestamp = datetime.datetime.today()

        dirPath = os.path.dirname( filePath )
        os.makedirs( dirPath, exist_ok=True )
        urllib.request.urlretrieve( url, filePath )
        persist.store_object_simple(currTimestamp, timestampPath)
        return (filePath, timestampPath)

    def getWorksheetFromFile(self, dataFile) -> DataFrame:
        _LOGGER.debug( "opening workbook: %s", dataFile )
        dataFrame = pandas.read_csv( dataFile, names=["name", "unknown_1", "date", "time", "kurs_otw",
                                                      "max", "min", "kurs", "obrot", "unknown_2"] )
        dataFrame.drop( dataFrame.tail(1).index, inplace=True )
        return dataFrame


## https://info.bossa.pl/index.jsp?layout=mstock&page=1&news_cat_id=706&dirpath=/ciagle/mstock/sesjacgl
class MetaStockEODData:

    def __init__(self):
        pass
