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
# import urllib.request
import datetime
from typing import List

import pandas
from pandas.core.frame import DataFrame

from stockdataaccess.dataaccess import TMP_DIR, download_html_content
from stockdataaccess.dataaccess.datatype import StockDataType
from stockdataaccess.dataaccess.worksheetdata import BaseWorksheetData,\
    WorksheetDAO
from stockdataaccess.synchronized import synchronized


_LOGGER = logging.getLogger(__name__)


class GpwArchiveData( BaseWorksheetData ):
    """Handle GPW archive data."""

    class GpwArchiveDAO( WorksheetDAO ):
        """Data access object."""

        def __init__(self, dayDate: datetime.date = None):
            super().__init__()
            if dayDate is not None:
                self.day = dayDate
            else:
                self.day = datetime.datetime.now().date()

        def getDataPath(self):
            date_year = self.day.year
            date_str  = self.day.strftime("%Y-%m-%d")
            return f"{TMP_DIR}data/gpw/arch/{date_year}/{date_str}.xls"

        ## override
        def downloadData(self, filePath):
            ## pattern example: https://www.gpw.pl/archiwum-notowan?fetch=1&type=10&instrument=&date=15-01-2020
            url = "https://www.gpw.pl/archiwum-notowan?fetch=1&type=10&instrument=&date="\
                + self.day.strftime("%d-%m-%Y")

            relPath = os.path.relpath( filePath )
            _LOGGER.debug( "grabbing data from url[%s] as file[%s]", url, relPath )
            # _LOGGER.debug( "grabbing data from url[%s] as file[%s]", url.split("?", maxsplit=1)[0], relPath )

            dirPath = os.path.dirname( filePath )
            os.makedirs( dirPath, exist_ok=True )

            try:
                download_html_content( url, filePath )
            except BaseException as ex:
                _LOGGER.exception( "unable to load object data -- %s: %s", type(ex), ex, exc_info=False )
                raise

        @synchronized
        def _parseDataFromFile(self, dataFile: str) -> DataFrame:
#             _LOGGER.debug( "opening workbook: %s", dataFile )
            dataFrame = pandas.read_excel( dataFile )
            # pylint: disable=E1101
            dataFrame.drop( dataFrame.tail(1).index, inplace=True )
            return dataFrame

#             try:
#     #             _LOGGER.debug( "opening file: %s", os.path.abspath(dataFile) )
#                 workbook = xlrd.open_workbook( dataFile )
#                 worksheet = workbook.sheet_by_index(0)
#     #             _LOGGER.debug( "found data for: %s", day )
#                 return worksheet
#             except xlrd.biffh.XLRDError as err:
#                 message = str(err)
#                 if "Unsupported format" not in message:
#                     _LOGGER.exception( "Error" )
#                     return None
#
#                 # Unsupported format
#                 if self.isFileWithNoData(dataFile) is False:
#                     _LOGGER.exception( "Error" )
#                     return None
#
#                 # Brak danych dla wybranych kryteriów.
#     #             _LOGGER.info("day without stock: %s", day )
#                 return None
#             return None

        @staticmethod
        def isFileWithNoData(filePath):
            with open( filePath, encoding="utf-8" ) as f:
                if "Brak danych dla wybranych kryteriów." in f.read():
                    return True
            return False

    ## ==========================================================

    def __init__(self, dayDate: datetime.date = None):
        dao = GpwArchiveData.GpwArchiveDAO( dayDate )
        super().__init__( dao )

    def sourceLink( self ):
        return "https://www.gpw.pl/archiwum-notowan"

    def getData(self, dataType: StockDataType, day: datetime.date = None):
        if day is not None:
            self.dao = GpwArchiveData.GpwArchiveDAO( day )

#         _LOGGER.debug( "getting max from date: %s", day )
        worksheet = self.getWorksheetData()
        if worksheet is None:
            return None
        colIndex = self.getDataColumnIndex( dataType )
        nameIndex = self.getDataColumnIndex( StockDataType.STOCK_NAME )
        names  = worksheet.iloc[:, nameIndex]
        values = worksheet.iloc[:, colIndex]
        return dict( zip(names, values) )

    ## check valid stock day starting from "day" and going past
    def getRecentValidDay(self, day: datetime.date) -> datetime.date:
        currDay = day
        worksheet = None
        while True:
            self.dao = GpwArchiveData.GpwArchiveDAO( currDay )
            worksheet = self.accessWorksheetData()
#             worksheet = self.getWorksheetData()        ## causes 'recent day' to be calculated badly
            if worksheet is not None:
                return currDay
            currDay -= datetime.timedelta(days=1)
        return None

    def getNextValidDay(self, day: datetime.date):
        currDay = day
        dayToday = datetime.date.today()
        worksheet = None
        while currDay < dayToday:
            self.dao = GpwArchiveData.GpwArchiveDAO( currDay )
            worksheet = self.getWorksheetData()
            if worksheet is not None:
                return currDay
            currDay += datetime.timedelta(days=1)
        return None

    def getStockData(self, isinList: List[str] = None):
        return self.getRowsByValueList( StockDataType.ISIN, isinList )

    def getRowByIsin(self, isin):
        return self.getRowByValue( StockDataType.ISIN, isin )

    def getIsinField(self, rowIndex: int):
        return self.getDataByIndex( StockDataType.ISIN, rowIndex )

    ## get column index
    ## override
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
        return self.getColumnIndex( columnType )

    @staticmethod
    def getColumnIndex( columnType: StockDataType ) -> int:
        switcher = {
            StockDataType.STOCK_NAME:      1,
            StockDataType.ISIN:            2,
            StockDataType.OPENING:         4,
            StockDataType.MAX:             5,
            StockDataType.MIN:             6,
            StockDataType.CLOSING:         7,
            StockDataType.VOLUME:          9
        }
        index = switcher.get(columnType, None)

        if index is None:
            raise ValueError( f"Invalid value: {columnType}" )
        return index

#     ################################################################
#
#     def getData(self, dataType: ArchiveDataType, day: datetime.date):
#         # _LOGGER.debug( "getting stock data for: %s", day )
#         worksheet = self.getWorksheet( day )
#         if worksheet is None:
#             _LOGGER.warning("worksheet not found for day: %s", day)
#             return None
#         _LOGGER.debug("worksheet found for day: %s", day )
#         colIndex = self.getColumnIndex( dataType )
#         if colIndex is None:
#             return None
#         return self.extractColumn( worksheet, colIndex )
#
#     ## check valid stock day starting from "day" and going past
#     def getRecentValidDay(self, day: datetime.date) -> datetime.date:
#         currDay = day
#         worksheet = None
#         while True:
#             worksheet = self.getWorksheet(currDay)
#             if worksheet is not None:
#                 return currDay
#             currDay -= datetime.timedelta(days=1)
#         return None
#
#     def getNextValidDay(self, day: datetime.date):
#         currDay = day
#         dayToday = datetime.date.today()
#         worksheet = None
#         while currDay < dayToday:
#             worksheet = self.getWorksheet(currDay)
#             if worksheet is not None:
#                 return currDay
#             currDay += datetime.timedelta(days=1)
#         return None
#
#     # ==========================================================================
#
#     @staticmethod
#     def getColumnIndex(dataType: ArchiveDataType):
#         switcher = {
#             ArchiveDataType.DATE:          0,
#             ArchiveDataType.NAME:          1,
#             ArchiveDataType.ISIN:          2,
#             ArchiveDataType.CURRENCY:      3,
#             ArchiveDataType.OPENING:       4,
#             ArchiveDataType.MAX:           5,
#             ArchiveDataType.MIN:           6,
#             ArchiveDataType.CLOSING:       7,
#             ArchiveDataType.CHANGE:        8,
#             ArchiveDataType.VOLUME:        9,
#             ArchiveDataType.TRANSACTIONS: 10,
#             ArchiveDataType.TRADING:      11
#         }
#         return switcher.get(dataType, None)
#
#     def extractColumn(self, worksheet, colIndex):
#         # name col: 1
#         # rows are indexed by 0, first row is header
#         ret = {}
#         nameIndex = self.getColumnIndex( ArchiveDataType.NAME )
#         for row in range(1, worksheet.nrows):
#             name = worksheet.cell(row, nameIndex).value
#             value = worksheet.cell(row, colIndex).value
#             ret[ name ] = value
#         return ret
