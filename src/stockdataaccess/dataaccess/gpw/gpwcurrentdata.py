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
import time
import random

from typing import List

import re
import pandas
from pandas.core.frame import DataFrame

from stockdataaccess.dataaccess import TMP_DIR
from stockdataaccess.dataaccess.datatype import StockDataType
from stockdataaccess.dataaccess.worksheetdata import WorksheetDAO,\
    BaseWorksheetDAO, BaseWorksheetData
from stockdataaccess.dataaccess.convert import apply_on_column, convert_float,\
    convert_int, cleanup_column
from stockdataaccess.dataaccess import download_html_content
from stockdataaccess.synchronized import synchronized
from stockdataaccess.pprint import fullname


_LOGGER = logging.getLogger(__name__)


class GpwCurrentStockData( BaseWorksheetData ):
    """Access GPW session current stock values."""

    class GpwCurrentStockDAO( WorksheetDAO ):
        """Data access object."""

        def getDataPath(self):
            return TMP_DIR + "data/gpw/recent_data.xls"

        ## override
        def downloadData(self, filePath):
            url = ("https://www.gpw.pl/ajaxindex.php"
                   "?action=GPWQuotations&start=showTable&tab=all&lang=PL&type=&full=1&format=html&download_xls=1")

            relPath = os.path.relpath( filePath )
            _LOGGER.debug( "grabbing data from url[%s] as file[%s]", url, relPath )
            # _LOGGER.debug( "grabbing data from url[%s] as file[%s]", url.split("?", maxsplit=1)[0], relPath )

            try:
                download_html_content( url, filePath )
            except BaseException as ex:
                _LOGGER.exception( "unable to load object data -- %s: %s", type(ex), ex, exc_info=False )
                raise

        @synchronized
        def _parseDataFromFile(self, dataFile: str) -> DataFrame:
#             _LOGGER.debug( "opening workbook: %s", dataFile )
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

            try:
                apply_on_column( dataFrame, 'Wol. obr. - skumul.', convert_int )
            except KeyError:
                _LOGGER.exception( "unable to get values by key" )

            try:
                apply_on_column( dataFrame, 'Wart. obr. - skumul.(tys.)', convert_float )
            except KeyError:
                _LOGGER.exception( "unable to get values by key" )

#             append_stock_isin( dataFrame, dataFile )

            return dataFrame

    ## ==========================================================

    def __init__(self):
        dao = GpwCurrentStockData.GpwCurrentStockDAO()
        super().__init__( dao )

    def sourceLink(self):
        return "https://www.gpw.pl/akcje"

    def getGrabTimestmp(self) -> datetime.datetime:
        return self.dao.getGrabTimestmp()

    def getStockData(self, tickerList: List[str] = None):
        return self.getRowsByValueList( StockDataType.TICKER, tickerList )

    def getData(self, dataType: StockDataType):
#         _LOGGER.debug( "getting max from date: %s", day )
        worksheet = self.getWorksheetData()
        if worksheet is None:
            return None
        colIndex = self.getDataColumnIndex( dataType )
        nameIndex = self.getDataColumnIndex( StockDataType.STOCK_NAME )
        names  = worksheet.iloc[:, nameIndex]
        values = worksheet.iloc[:, colIndex]
        return dict( zip(names, values) )

    def getRowByTicker(self, ticker):
        return self.getRowByValue( StockDataType.TICKER, ticker )

    def getTickerField(self, rowIndex: int):
        return self.getDataByIndex( StockDataType.TICKER, rowIndex )

    def getTickerFromIsin(self, stockIsin):
        return self.getDataByValue( StockDataType.ISIN, stockIsin, StockDataType.TICKER )

    def getTickerFromName(self, stockName):
        return self.getDataByValue( StockDataType.STOCK_NAME, stockName, StockDataType.TICKER )

    def getStockIsinFromTicker(self, ticker):
        return self.getDataByValue( StockDataType.TICKER, ticker, StockDataType.ISIN )

    def getNameFromTicker(self, ticker):
        return self.getDataByValue( StockDataType.TICKER, ticker, StockDataType.STOCK_NAME )

    def getNameFromIsin(self, stockIsin):
        return self.getDataByValue( StockDataType.ISIN, stockIsin, StockDataType.STOCK_NAME )

    def getTickerFieldByName(self, stockName):
        return self.getDataByValue( StockDataType.STOCK_NAME, stockName, StockDataType.TICKER )

    def getRecentValueByTicker(self, ticker):
        return self.getDataByValue( StockDataType.TICKER, ticker, StockDataType.RECENT_VALUE )

    def getRecentChangeByTicker(self, ticker):
        return self.getDataByValue( StockDataType.TICKER, ticker, StockDataType.CHANGE_TO_REF )

    def getReferenceValueByTicker(self, ticker):
        return self.getDataByValue( StockDataType.TICKER, ticker, StockDataType.REFERENCE )

    ## get column index
    ## override
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
#         switcher = {
#             StockDataType.STOCK_NAME: 0,
#             StockDataType.NO_DIV_DAY: 5
#         }
#         colIndex = switcher.get(columnType, None)

        colIndex = GpwCurrentStockData.getColumnIndex( columnType )
        if colIndex is None:
            raise ValueError( f"Invalid value: {columnType}" )
        return colIndex

    ## ======================================================================

    def getGpwLinkFromIsin(self, isin):
        return f"https://www.gpw.pl/spolka?isin={isin}"

    def getGoogleLinkFromTicker(self, ticker):
        infoLink = f"https://www.google.com/search?q=spolka+gpw+{ticker}"
        return infoLink

    def getMoneyLinkFromIsin(self, isin):
        return f"https://www.money.pl/gielda/spolki-gpw/{isin}.html"

    def getBankierLinkFromName(self, name):
        return f"https://www.bankier.pl/inwestowanie/profile/quote.html?symbol={name}"

    ## ======================================================================

    @staticmethod
    def getColumnIndex(dataType: StockDataType):
        switcher = {
            StockDataType.STOCK_NAME:         2,
            StockDataType.ISIN:               3,
            StockDataType.TICKER:             4,
            StockDataType.CURRENCY:           5,
            StockDataType.RECENT_TRANS_TIME:  6,
            StockDataType.REFERENCE:          7,
            StockDataType.TKO:                8,
            StockDataType.OPENING:            9,
            StockDataType.MIN:               10,
            StockDataType.MAX:               11,
            StockDataType.RECENT_VALUE:      12,
            StockDataType.CHANGE_TO_REF:     14
        }
        return switcher.get(dataType, None)

    ## returns value of recent transaction, if no transaction then returns reference vale
    @staticmethod
    def unitPrice( currentStockDataRow ):
        ## current value
        currUnitValueIndex = GpwCurrentStockData.getColumnIndex( StockDataType.RECENT_VALUE )
        currUnitValueRaw = currentStockDataRow.iloc[currUnitValueIndex]
        if currUnitValueRaw != "-":
            return float( currUnitValueRaw )

        ## TKO
#        tkoIndex = GpwCurrentStockData.getColumnIndex( StockDataType.TKO )
#        tkoValueRaw = currentStockDataRow.iloc[tkoIndex]
#        if tkoValueRaw != "-":
#            return float( tkoValueRaw )

        ## reference value
        return GpwCurrentStockData.unitReferencePrice( currentStockDataRow )

    @staticmethod
    def unitReferencePrice( currentStockDataRow ):
        ## reference value
        refValueIndex = GpwCurrentStockData.getColumnIndex( StockDataType.REFERENCE )
        refValueRaw = currentStockDataRow.iloc[refValueIndex]
        if refValueRaw != "-":
            return float( refValueRaw )
        return 0.0


# ============================================================================


class GpwCurrentIndexesData( BaseWorksheetData ):

    class GpwCurrentIndexesDAO( BaseWorksheetDAO ):
        """Data access object."""

        def __init__(self):
            self.worksheet: DataFrame = None
            self.dataList: List[ BaseWorksheetData ] = []
            self.dataList.append( GpwMainIndexesData() )
            self.dataList.append( GpwMacroIndexesData() )
            self.dataList.append( GpwSectorsIndexesData() )

        ## override
        @synchronized
        def loadWorksheet(self, preventDownload=False):
            for dataAccess in self.dataList[:-1]:
                dataAccess.loadWorksheet( preventDownload )
                ## set random sleep preventing "[Errno 104] Connection reset by peer"
                ## server seems to reset connection in case of detection of web scrapping
                randTime = 1.0 + random.random()
                time.sleep( randTime )
            ## last element (without sleep)
            dataAccess = self.dataList[-1]
            dataAccess.loadWorksheet( preventDownload )
            return self.getDataFrame()

        ## override
        def getDataFrame(self) -> DataFrame:
            self.worksheet = DataFrame()
            for dataAccess in self.dataList:
                dataFrame = dataAccess.getDataFrame()
#                 self.worksheet.concat( dataFrame, copy=False )
                self.worksheet = self.worksheet.append( dataFrame )
            return self.worksheet

    ## ==========================================================

    def __init__(self):
        dao = GpwCurrentIndexesData.GpwCurrentIndexesDAO()
        super().__init__( dao )

    def sourceLink(self):
        return "https://gpwbenchmark.pl/notowania"

    def getNameFromIsin(self, isin):
        return self.getDataByValue( StockDataType.ISIN, isin, StockDataType.STOCK_NAME )

    def getRecentValueByIsin(self, isin):
        return self.getDataByValue( StockDataType.ISIN, isin, StockDataType.RECENT_VALUE )

    def getRecentChangeByIsin(self, isin):
        return self.getDataByValue( StockDataType.ISIN, isin, StockDataType.CHANGE_TO_REF )

    def getRowByIsin(self, isin):
        return self.getRowByValue( StockDataType.ISIN, isin )

    ## get column index
    ## override
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
        switcher = {
            StockDataType.STOCK_NAME:     1,
            StockDataType.RECENT_VALUE:   8,
            StockDataType.CHANGE_TO_REF:  9,
            StockDataType.ISIN:          12
        }
        colIndex = switcher.get(columnType, None)
        if colIndex is None:
            raise ValueError( f"Invalid value: {columnType}" )
        return colIndex

    ## ======================================================================

    def getGpwLinkFromIsin(self, isin):
        return f"https://gpwbenchmark.pl/karta-indeksu?isin={isin}"
        #return "https://www.gpw.pl/spolka?isin=%s" % isin

    def getGoogleLinkFromName(self, name):
        infoLink = f"https://www.google.com/search?q=spolka+gpw+{name}"
        return infoLink

    def getMoneyLinkFromName(self, name):
        value = name.replace('-', '_')
        return f"https://www.money.pl/gielda/indeksy_gpw/{value}/"

    def getBankierLinkFromName(self, name):
        return f"https://www.bankier.pl/inwestowanie/profile/quote.html?symbol={name}"


class GpwMainIndexesData( BaseWorksheetData ):

    class GpwMainIndexesDAO( WorksheetDAO ):
        """Data access object."""

        def getDataPath(self):
            return f"{TMP_DIR}data/gpw/indexes_main_data.html"

        ## override
        def downloadData(self, filePath):
            url = "https://gpwbenchmark.pl/ajaxindex.php?action=GPWIndexes&start=showTable&tab=indexes&lang=PL"

            relPath = os.path.relpath( filePath )
            _LOGGER.debug( "grabbing data from url[%s] as file[%s]", url.split("?", maxsplit=1)[0], relPath )

            try:
                download_html_content( url, filePath )
            except BaseException as ex:
                _LOGGER.exception( "unable to load object data -- %s: %s", type(ex), ex, exc_info=False )
                raise
            # download_html_content( url, filePath )

        @synchronized
        def _parseDataFromFile(self, dataFile: str) -> DataFrame:
#             _LOGGER.debug( "opening workbook: %s", dataFile )
            allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
            dataFrame = DataFrame()
            dataFrame = dataFrame.append( allDataFrames[0] )        ## realtime indexes
            dataFrame = dataFrame.append( allDataFrames[1] )        ## main indexes
            convert_indexes_data( dataFrame )
            append_indexes_isin( dataFrame, dataFile )
            return dataFrame

    def __init__(self):
        dao = GpwMainIndexesData.GpwMainIndexesDAO()
        super().__init__( dao )

    ## get column index
    ## override
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
        raise ValueError( f"Invalid value: {columnType}" )


class GpwMacroIndexesData( BaseWorksheetData ):

    class GpwMacroIndexesDAO( WorksheetDAO ):
        """Data access object."""

        def getDataPath(self):
            return f"{TMP_DIR}data/gpw/indexes_macro_data.html"

        ## override
        def downloadData(self, filePath):
            url = "https://gpwbenchmark.pl/ajaxindex.php?action=GPWIndexes&start=showTable&tab=macroindices&lang=PL"

            relPath = os.path.relpath( filePath )
            _LOGGER.debug( "grabbing data from url[%s] as file[%s]", url.split("?", maxsplit=1)[0], relPath )

            try:
                download_html_content( url, filePath )
            except BaseException as ex:
                _LOGGER.exception( "unable to load object data -- %s: %s", fullname(ex), ex, exc_info=False )
                raise

        @synchronized
        def _parseDataFromFile(self, dataFile: str) -> DataFrame:
#             _LOGGER.debug( "opening workbook: %s", dataFile )
            allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
            dataFrame = allDataFrames[0]
            convert_indexes_data( dataFrame )
            append_indexes_isin( dataFrame, dataFile )
            return dataFrame

    def __init__(self):
        dao = GpwMacroIndexesData.GpwMacroIndexesDAO()
        super().__init__( dao )

    ## get column index
    ## override
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
        raise ValueError( f"Invalid value: {columnType}" )


class GpwSectorsIndexesData( BaseWorksheetData ):

    class GpwSectorsIndexesDAO( WorksheetDAO ):
        """Data access object."""

        def getDataPath(self):
            return f"{TMP_DIR}data/gpw/indexes_sectors_data.html"

        ## override
        def downloadData(self, filePath):
            url = "https://gpwbenchmark.pl/ajaxindex.php?action=GPWIndexes&start=showTable&tab=sectorbased&lang=PL"

            relPath = os.path.relpath( filePath )
            _LOGGER.debug( "grabbing data from url[%s] as file[%s]", url.split("?", maxsplit=1)[0], relPath )

            try:
                download_html_content( url, filePath )
            except BaseException as ex:
                _LOGGER.exception( "unable to load object data -- %s: %s", fullname(ex), ex, exc_info=False )
                raise

        @synchronized
        def _parseDataFromFile(self, dataFile: str) -> DataFrame:
#             _LOGGER.debug( "opening workbook: %s", dataFile )
            allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
            dataFrame = allDataFrames[0]
            convert_indexes_data( dataFrame )
            append_indexes_isin( dataFrame, dataFile )
            return dataFrame

    def __init__(self):
        dao = GpwSectorsIndexesData.GpwSectorsIndexesDAO()
        super().__init__( dao )

    ## get column index
    ## override
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
        raise ValueError( f"Invalid value: {columnType}" )


def convert_indexes_data( dataFrame: DataFrame ):
    apply_on_column( dataFrame, 'Kurs otw.', convert_float )
    apply_on_column( dataFrame, 'Kurs min.', convert_float )
    apply_on_column( dataFrame, 'Kurs maks.', convert_float )
    apply_on_column( dataFrame, 'Wart. ost.', convert_float )
    apply_on_column( dataFrame, 'Wartość obrotu skum. (w tys. zł)', convert_float )

    apply_on_column( dataFrame, 'Liczba spółek', convert_int )
    apply_on_column( dataFrame, '% otw. portfela', convert_int )


# ## find isin's in file and append to dataframe
# def append_stock_isin( dataFrame, dataFile ):
#     with open(dataFile, 'r', encoding="utf-8") as file:
#         fileContent = file.read()
#
#     isinList = []
#
#     for name in dataFrame["Nazwa"]:
#         # pylint: disable=W1401
#         pattern = r'<a\s*href="spolka\?isin=(\S*?)">' + name + r'.*?</a>'
#         matchObj = re.search( pattern, fileContent )
#         if matchObj is None:
#             isinList.append( None )
#             continue
#         groups = matchObj.groups()
#         if len(groups) < 1:
#             isinList.append( None )
#             continue
#         isin = groups[0]
#         isinList.append( isin )
#
#     dataFrame["isin"] = isinList


def append_indexes_isin( dataFrame, dataFile ):
    with open(dataFile, 'r', encoding="utf-8") as file:
        fileContent = file.read()

    isinList = []

    for short in dataFrame["Skrót"]:
        # pylint: disable=W1401
        pattern = r'<a href="/karta-indeksu\?isin=(\S*?)">' + short + r'</a>'
        matchObj = re.search( pattern, fileContent )
        if matchObj is None:
            isinList.append( None )
            continue
        groups = matchObj.groups()
        if len(groups) < 1:
            isinList.append( None )
            continue
        isin = groups[0]
        isinList.append( isin )

    dataFrame["ISIN"] = isinList
