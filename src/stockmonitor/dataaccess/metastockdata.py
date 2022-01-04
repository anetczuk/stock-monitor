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
import tempfile
import zipfile
import shutil

import pandas
from pandas.core.frame import DataFrame

from stockmonitor.dataaccess import tmp_dir
from stockmonitor.dataaccess.worksheetdata import WorksheetData, BaseWorksheetDAO
from stockmonitor.synchronized import synchronized


_LOGGER = logging.getLogger(__name__)


## https://info.bossa.pl/index.jsp?layout=intraday&page=1&news_cat_id=875&dirpath=/mstock/daily/
class MetaStockIntradayData( BaseWorksheetDAO ):
# class MetaStockIntradayData( BaseWorksheetData ):

    class DAO( WorksheetData ):
        """Data access object."""

        def __init__( self, dataDate: datetime.date=None ):
            super().__init__()
            if dataDate is None:
                dataDate = datetime.datetime.now().date()
            self.dataDate: datetime.date = dataDate

        @synchronized
        def getWorksheetForDate( self, dataDate: datetime.date, forceRefresh=False ):
            self.dataDate = dataDate
            return self.getWorksheetData( forceRefresh )

        def getDataPath(self):
            dateString = self.dataDate.isoformat()
            return tmp_dir + "data/bossa/intraday/%s.prn" % dateString
    
        def getDataUrl(self):
            dateString = self.dataDate.isoformat()
            return "https://info.bossa.pl/pub/intraday/mstock/daily//%s-tick.zip" % dateString
    
    #         if self.dataDate == currDate:
    #             ## https://info.bossa.pl/pub/intraday/mstock/daily//tick.zip
    #             return "https://info.bossa.pl/pub/intraday/mstock/daily//tick.zip"
    #         else:
    #             ## https://info.bossa.pl/pub/intraday/mstock/daily//2020-09-28-tick.zip
    #             dateString = self.dataDate.isoformat()
    #             return "https://info.bossa.pl/pub/intraday/mstock/daily//%s-tick.zip" % dateString
    
        ## override
        def _downloadContent( self, url, filePath ):
            zipPath = filePath + ".zip"
            super()._downloadContent( url, zipPath )
    
            ## extract downloaded file
            _LOGGER.debug( "extracting zip[%s]", zipPath )
            with tempfile.TemporaryDirectory() as tmpdir:
                zipMember = "a_cgl.prn"
                with zipfile.ZipFile( zipPath, 'r' ) as zip_ref:
                    zip_ref.extract( zipMember, path=tmpdir )
                    tmpFile = os.path.join( tmpdir, zipMember )
                    _LOGGER.debug( "moving extracted file[%s] to [%s]", tmpFile, filePath )
                    shutil.move( tmpFile, filePath )
    
        @synchronized
        def _parseDataFromFile(self, dataFile) -> DataFrame:
#             _LOGGER.debug( "opening workbook: %s", dataFile )
            dataFrame = pandas.read_csv( dataFile, names=["name", "unknown_1", "date", "time", "kurs_otw",
                                                          "max", "min", "kurs", "obrot", "unknown_2"] )
            dataFrame.drop( dataFrame.tail(1).index, inplace=True )
            return dataFrame
    

    def __init__(self, dataDate: datetime.date=None):
        dao = MetaStockIntradayData.DAO( dataDate )
        super().__init__( dao )

    def sourceLink(self):
        return "https://info.bossa.pl/notowania/pliki/intraday/metastock/"
    
    def getWorksheetForDate(self, dataDate, forceRefresh=False):
        return self.dao.getWorksheetForDate( dataDate, forceRefresh )


# ## https://info.bossa.pl/index.jsp?layout=mstock&page=1&news_cat_id=706&dirpath=/ciagle/mstock/sesjacgl
# class MetaStockEODData:
# 
#     def __init__(self):
#         pass
# 
#     def sourceLink(self):
#         return "https://info.bossa.pl/notowania/metastock/"
