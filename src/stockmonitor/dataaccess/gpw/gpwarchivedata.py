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

import urllib.error
import xlrd

from stockmonitor.dataaccess import tmp_dir, urlretrieve
from stockmonitor.dataaccess.datatype import ArchiveDataType


_LOGGER = logging.getLogger(__name__)


class GpwArchiveData:
    """Handle GPW archive data."""

    def sourceLink(self):
        return "https://www.gpw.pl/archiwum-notowan"

    def getData(self, dataType: ArchiveDataType, day: datetime.date):
        # _LOGGER.debug( "getting stock data for: %s", day )
        worksheet = self.getWorksheet( day )
        if worksheet is None:
            _LOGGER.warning("worksheet not found for day: %s", day)
            return None
        _LOGGER.debug("worksheet found for day: %s", day )
        colIndex = self.getColumnIndex( dataType )
        if colIndex is None:
            return None
        return self.extractColumn( worksheet, colIndex )

    ## check valid stock day starting from "day" and going past
    def getRecentValidDay(self, day: datetime.date) -> datetime.date:
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
        _LOGGER.debug( "getting data from date: %s", day )
        dataFile = self.downloadData( day )

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

    def downloadData(self, day):
        filePath = tmp_dir + "data/gpw/arch/" + day.strftime("%Y-%m-%d") + ".xls"
        if os.path.exists( filePath ):
            return filePath

        ## pattern example: https://www.gpw.pl/archiwum-notowan?fetch=1&type=10&instrument=&date=15-01-2020
        url = "https://www.gpw.pl/archiwum-notowan?fetch=1&type=10&instrument=&date=" + day.strftime("%d-%m-%Y")
        _LOGGER.debug( "grabbing data from utl: %s", url )

        dirPath = os.path.dirname( filePath )
        os.makedirs( dirPath, exist_ok=True )

        try:
            urlretrieve( url, filePath )

            return filePath
        except urllib.error.URLError as ex:
            _LOGGER.exception( "unable to access: %s %s", url, ex, exc_info=False )
            raise

    def isFileWithNoData(self, filePath):
        with open( filePath ) as f:
            if "Brak danych dla wybranych kryteriów." in f.read():
                return True
        return False
