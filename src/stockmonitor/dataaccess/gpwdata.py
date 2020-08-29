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
from stockmonitor.dataaccess.convert import convert_float, convert_int
from stockmonitor.dataaccess.datatype import ArchiveDataType, CurrentDataType
from stockmonitor.dataaccess.worksheetdata import WorksheetData, BaseWorksheetData


_LOGGER = logging.getLogger(__name__)


## =================================================================


class GpwArchiveData:
    """Handle GPW archive data."""

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

    ## check valid stock day starting from "day" and going past
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
        urllib.request.urlretrieve( url, filePath )
        return filePath

    def isFileWithNoData(self, filePath):
        with open( filePath ) as f:
            if "Brak danych dla wybranych kryteriów." in f.read():
                return True
        return False

    def sourceLink(self):
        return "https://www.gpw.pl/archiwum-notowan"


## ==========================================================================


def cleanup_column(dataFrame, colName):
    cleanup_column_str( dataFrame, colName, " " )
    cleanup_column_str( dataFrame, colName, "\t" )
    cleanup_column_str( dataFrame, colName, "\u00A0" )          ## non-breaking space
    cleanup_column_str( dataFrame, colName, "\xc2\xa0" )        ## non-breaking space


def cleanup_column_str(dataFrame, colName, substr):
    val = dataFrame.loc[ dataFrame[ colName ].str.contains( substr ), colName ]
    for index, value in val.items():
        val[ index ] = value.split( substr )[0]
    dataFrame.loc[ dataFrame[ colName ].str.contains( substr ), colName ] = val


class GpwCurrentData( WorksheetData ):
    """Handle GPW current day data."""

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

    def getRowByTicker(self, ticker):
        dataFrame = self.getWorksheet()
        if dataFrame is None:
            _LOGGER.warning("no worksheet found")
            return None
        colIndex = self.getColumnIndex( CurrentDataType.SHORT )
        retRows = dataFrame.loc[ dataFrame.iloc[:, colIndex] == ticker ]
        return retRows.squeeze()            ## convert 1 row dataframe to series

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

    ## ======================================================================

    def getGpwLinkFromIsin(self, isin):
        return "https://www.gpw.pl/spolka?isin=%s" % isin

    def getGoogleLinkFromCode(self, code):
        infoLink = "https://www.google.com/search?q=spolka+gpw+%s" % code
        return infoLink

    def getMoneyLinkFromIsin(self, isin):
        return "https://www.money.pl/gielda/spolki-gpw/%s.html" % isin

    def getIsinFromCode(self, code):
        _LOGGER.warning("unable to get isin: not implemented")
        #TODO: implement
        if code is None:
            return code
        return None

    ## ======================================================================

    def loadWorksheetFromFile(self, dataFile: str) -> DataFrame:
        _LOGGER.debug( "opening workbook: %s", dataFile )
        dataFrameList = pandas.read_html( dataFile, thousands='', decimal=',' )
        dataFrame = dataFrameList[0]

        ## flatten multi level header (column names)
        dataFrame.columns = dataFrame.columns.get_level_values(0)

        ## drop last row containing summary
        dataFrame.drop( dataFrame.tail(1).index, inplace=True )

        ## remove trash from column
        cleanup_column( dataFrame, 'Nazwa' )

        apply_on_column( dataFrame, 'Kurs odn.', convert_float )
        apply_on_column( dataFrame, 'Kurs otw.', convert_float )
        apply_on_column( dataFrame, 'Kurs min.', convert_float )
        apply_on_column( dataFrame, 'Kurs maks.', convert_float )
        apply_on_column( dataFrame, 'Kurs ost. trans. / zamk.', convert_float )
        apply_on_column( dataFrame, 'Zm.do k.odn.(%)', convert_float )

        ## Wart. obr. - skumul.(tys.)
        try:
            apply_on_column( dataFrame, 'Unnamed: 22_level_0', convert_float )
        except KeyError:
            _LOGGER.exception( "unable to get values by key" )

        ## Wol. obr. - skumul.
        try:
            apply_on_column( dataFrame, 'Unnamed: 21_level_0', convert_int )
        except KeyError:
            _LOGGER.exception( "unable to get values by key" )

        return dataFrame

    def getDataPaths(self):
        filePath      = tmp_dir + "data/gpw/recent_data.xls"
        timestampPath = tmp_dir + "data/gpw/recent_timestamp.txt"
        return (filePath, timestampPath)

    def getDataUrl(self):
        url = ("https://www.gpw.pl/ajaxindex.php"
               "?action=GPWQuotations&start=showTable&tab=all&lang=PL&full=1&format=html&download_xls=1")
        return url

    def sourceLink(self):
        return "https://www.gpw.pl/akcje"


## ==========================================================================


def convert_indexes_data( dataFrame: DataFrame ):
    apply_on_column( dataFrame, 'Kurs otw.', convert_float )
    apply_on_column( dataFrame, 'Kurs min.', convert_float )
    apply_on_column( dataFrame, 'Kurs maks.', convert_float )
    apply_on_column( dataFrame, 'Wart. ost.', convert_float )
    apply_on_column( dataFrame, 'Wartość obrotu skum. (w tys. zł)', convert_float )

    apply_on_column( dataFrame, 'Liczba spółek', convert_int )
    apply_on_column( dataFrame, '% otw. portfela', convert_int )


class GpwMainIndexesData( WorksheetData ):

    def loadWorksheetFromFile(self, dataFile: str) -> DataFrame:
        _LOGGER.debug( "opening workbook: %s", dataFile )
        allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
        dataFrame = DataFrame()
        dataFrame = dataFrame.append( allDataFrames[0] )        ## realtime indexes
        dataFrame = dataFrame.append( allDataFrames[1] )        ## main indexes
        convert_indexes_data( dataFrame )
        return dataFrame

    def getDataPaths(self):
        filePath      = tmp_dir + "data/gpw/indexes_main_data.html"
        timestampPath = tmp_dir + "data/gpw/indexes_main_timestamp.txt"
        return (filePath, timestampPath)

    def getDataUrl(self):
        url = "https://gpwbenchmark.pl/ajaxindex.php?action=GPWIndexes&start=showTable&tab=indexes&lang=PL"
        return url


class GpwMacroIndexesData( WorksheetData ):

    def loadWorksheetFromFile(self, dataFile: str) -> DataFrame:
        _LOGGER.debug( "opening workbook: %s", dataFile )
        allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
        dataFrame = allDataFrames[0]
        convert_indexes_data( dataFrame )
        return dataFrame

    def getDataPaths(self):
        filePath      = tmp_dir + "data/gpw/indexes_macro_data.html"
        timestampPath = tmp_dir + "data/gpw/indexes_macro_timestamp.txt"
        return (filePath, timestampPath)

    def getDataUrl(self):
        url = "https://gpwbenchmark.pl/ajaxindex.php?action=GPWIndexes&start=showTable&tab=macroindices&lang=PL"
        return url


class GpwSectorsIndexesData( WorksheetData ):

    def loadWorksheetFromFile(self, dataFile: str) -> DataFrame:
        _LOGGER.debug( "opening workbook: %s", dataFile )
        allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
        dataFrame = allDataFrames[0]
        convert_indexes_data( dataFrame )
        return dataFrame

    def getDataPaths(self):
        filePath      = tmp_dir + "data/gpw/indexes_sectors_data.html"
        timestampPath = tmp_dir + "data/gpw/indexes_sectors_timestamp.txt"
        return (filePath, timestampPath)

    def getDataUrl(self):
        url = "https://gpwbenchmark.pl/ajaxindex.php?action=GPWIndexes&start=showTable&tab=sectorbased&lang=PL"
        return url


class GpwIndexesData( BaseWorksheetData ):

    def __init__(self):
        super().__init__()
        self.dataList = list()
        self.dataList.append( GpwMainIndexesData() )
        self.dataList.append( GpwMacroIndexesData() )
        self.dataList.append( GpwSectorsIndexesData() )

    def loadWorksheet(self, forceRefresh=False):
        self.worksheet = DataFrame()
        for dataAccess in self.dataList:
            dataFrame = dataAccess.getWorksheet( forceRefresh )
            self.worksheet = self.worksheet.append( dataFrame )

    def downloadData(self):
        for dataAccess in self.dataList:
            dataAccess.downloadData()

    def sourceLink(self):
        return "https://gpwbenchmark.pl/notowania"


## ==========================================================================


## https://www.gpw.pl/wskazniki
class GpwIndicatorsData( WorksheetData ):

    def getStockIsin(self, rowIndex):
        dataFrame = self.getWorksheet()
        tickerColumn = dataFrame["Kod"]
        return tickerColumn.iloc[ rowIndex ]

    def loadWorksheetFromFile(self, dataFile: str) -> DataFrame:
        _LOGGER.debug( "opening workbook: %s", dataFile )
        allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
        dataFrame = DataFrame()
        dataFrame = dataFrame.append( allDataFrames[1] )            ## country
        dataFrame = dataFrame.append( allDataFrames[2] )            ## foreign

        cleanup_column( dataFrame, 'Sektor' )

        apply_on_column( dataFrame, 'Liczba wyemitowanych akcji', convert_int )
        apply_on_column( dataFrame, 'Wartość rynkowa (mln zł)', convert_float )
        apply_on_column( dataFrame, 'Wartość księgowa (mln zł)', convert_float )

        apply_on_column( dataFrame, 'C/WK', convert_float )
        apply_on_column( dataFrame, 'C/Z', convert_float )
        apply_on_column( dataFrame, 'Stopa dywidendy (%)', convert_float )

        return dataFrame

    def getDataPaths(self):
        filePath      = tmp_dir + "data/gpw/indicators_data.html"
        timestampPath = tmp_dir + "data/gpw/indicators_timestamp.txt"
        return (filePath, timestampPath)

    def getDataUrl(self):
        url = "https://www.gpw.pl/wskazniki"
        return url

    def sourceLink(self):
        return self.getDataUrl()


## ==========================================================================


## http://infostrefa.com/infostrefa/pl/spolki
class GpwIsinMapData( WorksheetData ):

    def getStockCodeFromIsin(self, stockIsin):
        dataFrame = self.getWorksheet()
        rowIndexes = dataFrame[ dataFrame["ISIN"] == stockIsin ].index.values
        if not rowIndexes:
            return None
        rowIndex = rowIndexes[0]
        tickerColumn = dataFrame["Ticker"]
        return tickerColumn.iloc[ rowIndex ]

    def getStockCodeFromName(self, stockName):
        dataFrame = self.getWorksheet()
        rowIndexes = dataFrame[ dataFrame["Nazwa giełdowa"] == stockName ].index.values
        if not rowIndexes:
            return None
        rowIndex = rowIndexes[0]
        tickerColumn = dataFrame["Ticker"]
        return tickerColumn.iloc[ rowIndex ]

    def getStockIsinFromCode(self, stockCode):
        dataFrame = self.getWorksheet()
        rowIndexes = dataFrame[ dataFrame["Ticker"] == stockCode ].index.values
        if not rowIndexes:
            return None
        rowIndex = rowIndexes[0]
        tickerColumn = dataFrame["ISIN"]
        return tickerColumn.iloc[ rowIndex ]

    def loadWorksheetFromFile(self, dataFile: str) -> DataFrame:
        _LOGGER.debug( "opening workbook: %s", dataFile )
        allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
        dataFrame = allDataFrames[1]
        return dataFrame

    def getDataPaths(self):
        filePath      = tmp_dir + "data/gpw/isin_map_data.html"
        timestampPath = tmp_dir + "data/gpw/isin_map_timestamp.txt"
        return (filePath, timestampPath)

    def getDataUrl(self):
        url = "http://infostrefa.com/infostrefa/pl/spolki"
        return url


## ============================================================


def apply_on_column( dataFrame, columnName, function ):
    dataFrame[ columnName ] = dataFrame[ columnName ].apply( function )
