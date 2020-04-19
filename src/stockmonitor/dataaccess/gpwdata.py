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
from datetime import date

import xlrd
import datetime

from stockmonitor.dataaccess.datatype import DataType


_LOGGER = logging.getLogger(__name__)


class GpwCrawler:
    """Download data from GPW webpage."""

    def __init__(self):
        pass

    ## Brak danych dla wybranych kryteriów.

    def getStockData(self, day):
        file = "./../tmp/data/gpw/" + day.strftime("%Y-%m-%d") + ".xls"
        if os.path.exists( file ):
            return file

        ## pattern example: https://www.gpw.pl/archiwum-notowan?fetch=1&type=10&instrument=&date=15-01-2020
        url = "https://www.gpw.pl/archiwum-notowan?fetch=1&type=10&instrument=&date=" + day.strftime("%d-%m-%Y")
        _LOGGER.debug( "grabbing data from utl: %s", url )

        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )
        urllib.request.urlretrieve( url, file )
        return file


class GpwData:
    """Handle GPW data."""

    def __init__(self):
        self.crawler = GpwCrawler()

    def getData(self, dataType: DataType, day: date):
#         _LOGGER.debug( "getting max from date: %s", day )
        worksheet = self.getWorksheet(day)
        if worksheet is None:
            return None
        colIndex = self.getColumnIndex( dataType )
#         _LOGGER.debug("yyyyyyyy %s %s %s", day, dataType, colIndex )
        if colIndex is None:
            return None
        return self.extractColumn( worksheet, colIndex )

    def getPrevValidDay(self, day: date):
        currDay = day
        worksheet = None
        while True:
            worksheet = self.getWorksheet(currDay)
            if worksheet is not None:
                return currDay
            currDay -= datetime.timedelta(days=1)
        return None

    def getNextValidDay(self, day: date):
        currDay = day
        dayToday = date.today()
        worksheet = None
        while currDay < dayToday:
            worksheet = self.getWorksheet(currDay)
            if worksheet is not None:
                return currDay
            currDay += datetime.timedelta(days=1)
        return None

    # ==========================================================================

    def getColumnIndex(self, dataType: DataType):
        switcher = {
            DataType.DATE:          0,
            DataType.NAME:          1,
            DataType.ISIN:          2,
            DataType.CURRENCY:      3,
            DataType.OPENING:       4,
            DataType.MAX:           5,
            DataType.MIN:           6,
            DataType.CLOSING:       7,
            DataType.CHANGE:        8,
            DataType.VOLUME:        9,
            DataType.TRANSACTIONS: 10,
            DataType.TRADING:      11
        }
        return switcher.get(dataType, None)

    def extractColumn(self, worksheet, colIndex):
        # name col: 1
        # rows are indexed by 0, first row is header
        ret = dict()
        for row in range(1, worksheet.nrows):
            name = worksheet.cell(row, 1).value
            value = worksheet.cell(row, colIndex).value
            ret[ name ] = value
        return ret

    def getWorksheet(self, day: date):
#         _LOGGER.debug( "getting data from date: %s", day )
        dataFile = self.crawler.getStockData( day )

        try:
            workbook = xlrd.open_workbook( dataFile )
            worksheet = workbook.sheet_by_index(0)
            _LOGGER.debug( "getting data from date: %s", day )
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
