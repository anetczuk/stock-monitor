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
import urllib.request
import datetime

from typing import List

import pandas
from pandas.core.frame import DataFrame
import xlrd

from stockmonitor.dataaccess import tmp_dir
from stockmonitor.dataaccess.datatype import ArchiveDataType, CurrentDataType
from stockmonitor import persist


_LOGGER = logging.getLogger(__name__)


class GpwArchiveCrawler:
    """Download archive data from GPW webpage."""

    def __init__(self):
        pass

    ## Brak danych dla wybranych kryteriów.

    def getStockData(self, day):
        filePath = tmp_dir + "data/gpw/arch/" + day.strftime("%Y-%m-%d") + ".xls"
        if os.path.exists( filePath ):
            return filePath

        ## pattern example: https://www.gpw.pl/archiwum-notowan?fetch=1&type=10&instrument=&date=15-01-2020
        url = "https://www.gpw.pl/archiwum-notowan?fetch=1&type=10&instrument=&date=" + day.strftime("%d-%m-%Y")
        _LOGGER.debug( "grabbing data from utl: %s", url )

        dirPath = os.path.dirname( filePath )
        os.makedirs( dirPath, exist_ok=True )
        urllib.request.urlretrieve( url, filePath )
        return filePath


class GpwCurrentCrawler:
    """Download current data from GPW webpage."""

    def __init__(self):
        pass

    ## Brak danych dla wybranych kryteriów.

    def getStockData(self, forceRefresh=False):
#         timeNow = datetime.datetime.now()
        # filePath = tmp_dir + "data/gpw/curr/" + timeNow.strftime("%Y-%m-%d_%H-%M-%S") + ".xls"
        filePath      = tmp_dir + "data/gpw/recent_data.xls"
        timestampPath = tmp_dir + "data/gpw/recent_timestamp.txt"
        if forceRefresh is False and os.path.exists( filePath ):
            _LOGGER.debug( "loading recent data from file[%s]", filePath )
            return (filePath, timestampPath)

        url = ("https://www.gpw.pl/ajaxindex.php"
               "?action=GPWQuotations&start=showTable&tab=all&lang=PL&full=1&format=html&download_xls=1")
        _LOGGER.debug( "grabbing data from utl[%s] to file[%s]", url, filePath )

        currTimestamp = datetime.datetime.today()

        dirPath = os.path.dirname( filePath )
        os.makedirs( dirPath, exist_ok=True )
        urllib.request.urlretrieve( url, filePath )
        persist.store_object_simple(currTimestamp, timestampPath)
        return (filePath, timestampPath)


class GpwArchiveData:
    """Handle GPW archive data."""

    def __init__(self):
        self.crawler = GpwArchiveCrawler()

    def getData(self, dataType: ArchiveDataType, day: datetime.date):
        _LOGGER.debug( "getting stock data for: %s", day )
        worksheet = self.getWorksheet( day )
        if worksheet is None:
            _LOGGER.warning("worksheet not found for day: %s", day)
            return None
        _LOGGER.debug("worksheet found for day: %s", day )
        colIndex = self.getColumnIndex( dataType )
        if colIndex is None:
            return None
        return self.extractColumn( worksheet, colIndex )

    ## check valid stock day starting from "day" and goind past
    def getRecentValidDay(self, day: datetime.date):
        currDay = day
        worksheet = None
        while True:
            worksheet = self.getWorksheet(currDay)
            if worksheet is not None:
                return currDay
            currDay -= datetime.timedelta(days=1)
        return None

    def getNextValidDay(self, day: datetime.date):
        currDay = day
        dayToday = datetime.date.today()
        worksheet = None
        while currDay < dayToday:
            worksheet = self.getWorksheet(currDay)
            if worksheet is not None:
                return currDay
            currDay += datetime.timedelta(days=1)
        return None

    # ==========================================================================

    def getColumnIndex(self, dataType: ArchiveDataType):
        switcher = {
            ArchiveDataType.DATE:          0,
            ArchiveDataType.NAME:          1,
            ArchiveDataType.ISIN:          2,
            ArchiveDataType.CURRENCY:      3,
            ArchiveDataType.OPENING:       4,
            ArchiveDataType.MAX:           5,
            ArchiveDataType.MIN:           6,
            ArchiveDataType.CLOSING:       7,
            ArchiveDataType.CHANGE:        8,
            ArchiveDataType.VOLUME:        9,
            ArchiveDataType.TRANSACTIONS: 10,
            ArchiveDataType.TRADING:      11
        }
        return switcher.get(dataType, None)

    def extractColumn(self, worksheet, colIndex):
        # name col: 1
        # rows are indexed by 0, first row is header
        ret = dict()
        nameIndex = self.getColumnIndex( ArchiveDataType.NAME )
        for row in range(1, worksheet.nrows):
            name = worksheet.cell(row, nameIndex).value
            value = worksheet.cell(row, colIndex).value
            ret[ name ] = value
        return ret

    def getWorksheet(self, day: datetime.date):
#         _LOGGER.debug( "getting data from date: %s", day )
        dataFile = self.crawler.getStockData( day )

        try:
#             _LOGGER.debug( "opening file: %s", os.path.abspath(dataFile) )
            workbook = xlrd.open_workbook( dataFile )
            worksheet = workbook.sheet_by_index(0)
#             _LOGGER.debug( "found data for: %s", day )
            return worksheet
        except xlrd.biffh.XLRDError as err:
            message = str(err)
            if "Unsupported format" not in message:
                _LOGGER.exception( "Error" )
                return None

            # Unsupported format
            if self.isFileWithNoData(dataFile) is False:
                _LOGGER.exception( "Error" )
                return None

            # Brak danych dla wybranych kryteriów.
#             _LOGGER.info("day without stock: %s", day )
            return None
        return None

    def isFileWithNoData(self, filePath):
        with open( filePath ) as f:
            if "Brak danych dla wybranych kryteriów." in f.read():
                return True
        return False


class GpwCurrentData:
    """Handle GPW current day data."""

    def __init__(self):
        self.crawler = GpwCurrentCrawler()
        self.worksheet: DataFrame = None
        self.grabTimestamp: datetime.datetime = None

    def refreshData(self):
        self.loadWorksheet( True )

    def getStockData(self, stockCodesList: List[str] = None) -> DataFrame:
        if stockCodesList is None:
            return None
        dataFrame = self.getWorksheet()
        if dataFrame is None:
            return None
        colIndex = self.getColumnIndex( CurrentDataType.SHORT )
        retRows = dataFrame.loc[ dataFrame.iloc[:, colIndex].isin( stockCodesList ) ]
        return retRows

    def getData(self, dataType: CurrentDataType):
#         _LOGGER.debug( "getting max from date: %s", day )
        worksheet = self.getWorksheet()
        if worksheet is None:
            return None
        colIndex = self.getColumnIndex( dataType )
        _LOGGER.debug("getting column data: %s %s", dataType, colIndex )
        if colIndex is None:
            return None
        return self.extractColumn( worksheet, colIndex )

    def getShortField(self, rowIndex: int):
        dataFrame = self.getWorksheet()
        if dataFrame is None:
            return None
        return self.getShortFieldFromData( dataFrame, rowIndex )

    def getShortFieldByName(self, stockName):
        dataFrame = self.getWorksheet()
        if dataFrame is None:
            return None
        nameIndex = self.getColumnIndex( CurrentDataType.NAME )
        shortIndex = self.getColumnIndex( CurrentDataType.SHORT )
        retRows = dataFrame.loc[ dataFrame.iloc[:, nameIndex] == stockName ]
        if retRows.shape[0] > 0:
            return retRows.iloc[0, shortIndex]
        return None

    def getShortFieldFromData(self, dataFrame: DataFrame, rowIndex: int):
        colIndex = self.getColumnIndex( CurrentDataType.SHORT )
        if colIndex is None:
            return None
        return dataFrame.iloc[rowIndex, colIndex]

    # ==========================================================================

    def getColumnIndex(self, dataType: CurrentDataType):
        switcher = {
            CurrentDataType.NAME:               2,
            CurrentDataType.SHORT:              3,
            CurrentDataType.CURRENCY:           4,
            CurrentDataType.RECENT_TRANS_TIME:  5,
            CurrentDataType.REFERENCE:          6,
            CurrentDataType.OPENING:            8,
            CurrentDataType.MIN:                9,
            CurrentDataType.MAX:               10,
            CurrentDataType.RECENT_TRANS:      11
        }
        return switcher.get(dataType, None)

    def extractColumn(self, worksheet, colIndex):
        # name col: 1
        # rows are indexed by 0, first row is header
        nameIndex = self.getColumnIndex( CurrentDataType.NAME )
#         ret = dict()
#         nrows = worksheet.shape[0]
#         for row in range(1, nrows):
#             name = worksheet.iat(row, nameIndex).value
#             value = worksheet.iat(row, colIndex).value
#             ret[ name ] = value
        names  = worksheet.iloc[:, nameIndex]
        values = worksheet.iloc[:, colIndex]
        return dict( zip(names, values) )

    def getWorksheet(self, forceRefresh=False) -> DataFrame:
        if self.worksheet is None or forceRefresh is True:
            self.loadWorksheet( forceRefresh )
        return self.worksheet

    def loadWorksheet(self, forceRefresh=False):
        dataFile, timestampFile = self.crawler.getStockData( forceRefresh )
        self.worksheet = self.loadWorksheetFromFile( dataFile )
        if timestampFile is not None:
            self.grabTimestamp = persist.load_object_simple( timestampFile, None )
        else:
            self.grabTimestamp = None

    def loadWorksheetFromFile(self, dataFile) -> DataFrame:
        _LOGGER.debug( "opening workbook: %s", dataFile )
        dataFrameList = pandas.read_html( dataFile, thousands='', decimal=',' )
        dataFrame = dataFrameList[0]
        dataFrame.drop( dataFrame.tail(1).index, inplace=True )
        return dataFrame

    def isFileWithNoData(self, _):
#         with open( filePath ) as f:
#             if "Brak danych dla wybranych kryteriów." in f.read():
#                 return True
        return False

    ## ======================================================================

    def getInfoLinkFromIsin(self, isin):
        return "https://www.gpw.pl/spolka?isin=%s" % isin

    def getInfoLinkFromCode(self, code):
        isin = self.getIsinFromCode(code)
        if isin is not None:
            infoLink = "https://www.gpw.pl/spolka?isin=%s" % isin
            return infoLink
        infoLink = "https://www.google.com/search?q=spolka+gpw+%s" % code
        return infoLink

    def getIsinFromCode(self, code):
        if code is None:
            return code
        return None
