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
import datetime

from typing import List

import re
import pandas
from pandas.core.frame import DataFrame

from stockmonitor.dataaccess import tmp_dir
from stockmonitor.dataaccess.datatype import StockDataType
from stockmonitor.dataaccess.worksheetdata import WorksheetData,\
    BaseWorksheetData, WorksheetDAO
from stockmonitor.dataaccess.convert import apply_on_column, convert_float,\
    convert_int, cleanup_column
from stockmonitor.synchronized import synchronized


_LOGGER = logging.getLogger(__name__)


class GpwCurrentStockData( WorksheetDAO ):
    """Handle GPW current day data."""

    class DAO( WorksheetData ):
        """Data access object."""
    
        def getDataPath(self):
            return tmp_dir + "data/gpw/recent_data.xls"
    
        def getDataUrl(self):
            url = ("https://www.gpw.pl/ajaxindex.php"
                   "?action=GPWQuotations&start=showTable&tab=all&lang=PL&full=1&format=html&download_xls=1")
            return url
    
        @synchronized
        def _parseDataFromFile(self, dataFile: str) -> DataFrame:
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
    
            try:
                apply_on_column( dataFrame, 'Wol. obr. - skumul.', convert_int )
            except KeyError:
                _LOGGER.exception( "unable to get values by key" )
    
            try:
                apply_on_column( dataFrame, 'Wart. obr. - skumul.(tys.)', convert_float )
            except KeyError:
                _LOGGER.exception( "unable to get values by key" )
    
            append_stock_isin( dataFrame, dataFile )
    
            return dataFrame


    def __init__(self):
        dao = GpwCurrentStockData.DAO()
        super().__init__( dao )

    def sourceLink(self):
        return "https://www.gpw.pl/akcje"

    def getStockData(self, tickerList: List[str] = None) -> DataFrame:
        if tickerList is None:
            return None
        dataFrame = self.getWorksheetData()
        if dataFrame is None:
            return None
        colIndex = GpwCurrentStockData.getColumnIndex( StockDataType.TICKER )
        retRows = dataFrame.loc[ dataFrame.iloc[:, colIndex].isin( tickerList ) ]
        return retRows

    def getData(self, dataType: StockDataType):
#         _LOGGER.debug( "getting max from date: %s", day )
        worksheet = self.getWorksheetData()
        if worksheet is None:
            return None
        colIndex = self.getColumnIndex( dataType )
        _LOGGER.debug("getting column data: %s %s", dataType, colIndex )
        if colIndex is None:
            return None
        return self.extractColumn( worksheet, colIndex )

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
        return self.getDataByValue( StockDataType.TICKER, ticker, StockDataType.RECENT_TRANS )

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

        colIndex = self.getColumnIndex( columnType )
        if colIndex is None:
            raise ValueError( 'Invalid value: %s' % ( columnType ) )
        return colIndex

    # ==========================================================================

    def extractColumn(self, worksheet, colIndex):
        # name col: 1
        # rows are indexed by 0, first row is header
        nameIndex = GpwCurrentStockData.getColumnIndex( StockDataType.STOCK_NAME )
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

    def getGoogleLinkFromTicker(self, ticker):
        infoLink = "https://www.google.com/search?q=spolka+gpw+%s" % ticker
        return infoLink

    def getMoneyLinkFromIsin(self, isin):
        return "https://www.money.pl/gielda/spolki-gpw/%s.html" % isin

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
            StockDataType.RECENT_TRANS:      12,
            StockDataType.CHANGE_TO_REF:     14
        }
        return switcher.get(dataType, None)

    ## returns value of recent transaction, if no transaction then returns reference vale
    @staticmethod
    def unitPrice( dataRow ):
        ## current value
        currUnitValueIndex = GpwCurrentStockData.getColumnIndex( StockDataType.RECENT_TRANS )
        currUnitValueRaw = dataRow.iloc[currUnitValueIndex]
        if currUnitValueRaw != "-":
            return float( currUnitValueRaw )

        ## TKO
#        tkoIndex = GpwCurrentStockData.getColumnIndex( StockDataType.TKO )
#        tkoValueRaw = dataRow.iloc[tkoIndex]
#        if tkoValueRaw != "-":
#            return float( tkoValueRaw )

        ## reference value
        return GpwCurrentStockData.unitReferencePrice( dataRow )

    @staticmethod
    def unitReferencePrice( dataRow ):
        ## reference value
        refValueIndex = GpwCurrentStockData.getColumnIndex( StockDataType.REFERENCE )
        refValueRaw = dataRow.iloc[refValueIndex]
        if refValueRaw != "-":
            return float( refValueRaw )
        return 0.0


# ============================================================================


class GpwCurrentIndexesData( BaseWorksheetData ):

    def __init__(self):
        super().__init__()
        self.worksheet: DataFrame = None
        self.dataList = list()
        self.dataList.append( GpwMainIndexesData() )
        self.dataList.append( GpwMacroIndexesData() )
        self.dataList.append( GpwSectorsIndexesData() )

    def sourceLink(self):
        return "https://gpwbenchmark.pl/notowania"

    ## override
    def getDataFrame(self) -> DataFrame:
        return self.worksheet

    def getNameFromIsin(self, isin):
        row = self.getRowByIsin( isin )
        colIndex = GpwCurrentStockData.getColumnIndex( StockDataType.STOCK_NAME )
        return row.iloc[ colIndex ]

    def getRecentValueByIsin(self, isin):
        row = self.getRowByIsin( isin )
        colIndex = GpwCurrentStockData.getColumnIndex( StockDataType.RECENT_TRANS )
        return row.iloc[ colIndex ]

    def getRecentChangeByIsin(self, isin):
        row = self.getRowByIsin( isin )
        if row is None or row.empty:
            return None
        colIndex = GpwCurrentStockData.getColumnIndex( StockDataType.CHANGE_TO_REF )
        return row.iloc[ colIndex ]

    def getRowByIsin(self, isin):
        dataFrame = self.getWorksheetData()
        if dataFrame is None or dataFrame.empty:
            _LOGGER.warning("no worksheet found")
            return None
        colIndex = GpwCurrentStockData.getColumnIndex( StockDataType.ISIN )
        isinColumn = dataFrame.iloc[ :, colIndex ]
        retRows = dataFrame.loc[ isinColumn == isin ]
        return retRows.squeeze()            ## convert 1 row dataframe to series

    def downloadData(self):
        for dataAccess in self.dataList:
            dataAccess.downloadData()

    ## override
    @synchronized
    def loadWorksheet(self):
        self.worksheet = DataFrame()
        for dataAccess in self.dataList:
            dataAccess.loadWorksheet()
            dataFrame = dataAccess.getDataFrame()
            self.worksheet = self.worksheet.append( dataFrame )

    ## ======================================================================

    def getGpwLinkFromIsin(self, isin):
        return "https://gpwbenchmark.pl/karta-indeksu?isin=%s" % isin
        #return "https://www.gpw.pl/spolka?isin=%s" % isin

    def getGoogleLinkFromName(self, name):
        infoLink = "https://www.google.com/search?q=spolka+gpw+%s" % name
        return infoLink

    def getMoneyLinkFromName(self, name):
        value = name.replace('-', '_')
        return "https://www.money.pl/gielda/indeksy_gpw/%s/" % value


class GpwMainIndexesData( WorksheetDAO ):

    class DAO( WorksheetData ):
        """Data access object."""
    
        def getDataPath(self):
            return tmp_dir + "data/gpw/indexes_main_data.html"
    
        def getDataUrl(self):
            url = "https://gpwbenchmark.pl/ajaxindex.php?action=GPWIndexes&start=showTable&tab=indexes&lang=PL"
            return url
    
        @synchronized
        def _parseDataFromFile(self, dataFile: str) -> DataFrame:
            _LOGGER.debug( "opening workbook: %s", dataFile )
            allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
            dataFrame = DataFrame()
            dataFrame = dataFrame.append( allDataFrames[0] )        ## realtime indexes
            dataFrame = dataFrame.append( allDataFrames[1] )        ## main indexes
            convert_indexes_data( dataFrame )
            append_indexes_isin( dataFrame, dataFile )
            return dataFrame

    def __init__(self):
        dao = GpwMainIndexesData.DAO()
        super().__init__( dao )


class GpwMacroIndexesData( WorksheetDAO ):

    class DAO( WorksheetData ):
        """Data access object."""

        def getDataPath(self):
            return tmp_dir + "data/gpw/indexes_macro_data.html"
    
        def getDataUrl(self):
            url = "https://gpwbenchmark.pl/ajaxindex.php?action=GPWIndexes&start=showTable&tab=macroindices&lang=PL"
            return url
    
        @synchronized
        def _parseDataFromFile(self, dataFile: str) -> DataFrame:
            _LOGGER.debug( "opening workbook: %s", dataFile )
            allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
            dataFrame = allDataFrames[0]
            convert_indexes_data( dataFrame )
            append_indexes_isin( dataFrame, dataFile )
            return dataFrame

    def __init__(self):
        dao = GpwMacroIndexesData.DAO()
        super().__init__( dao )


class GpwSectorsIndexesData( WorksheetDAO ):

    class DAO( WorksheetData ):
        """Data access object."""
    
        def getDataPath(self):
            return tmp_dir + "data/gpw/indexes_sectors_data.html"
    
        def getDataUrl(self):
            return "https://gpwbenchmark.pl/ajaxindex.php?action=GPWIndexes&start=showTable&tab=sectorbased&lang=PL"
    
        @synchronized
        def _parseDataFromFile(self, dataFile: str) -> DataFrame:
            _LOGGER.debug( "opening workbook: %s", dataFile )
            allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
            dataFrame = allDataFrames[0]
            convert_indexes_data( dataFrame )
            append_indexes_isin( dataFrame, dataFile )
            return dataFrame

    def __init__(self):
        dao = GpwSectorsIndexesData.DAO()
        super().__init__( dao )


def convert_indexes_data( dataFrame: DataFrame ):
    apply_on_column( dataFrame, 'Kurs otw.', convert_float )
    apply_on_column( dataFrame, 'Kurs min.', convert_float )
    apply_on_column( dataFrame, 'Kurs maks.', convert_float )
    apply_on_column( dataFrame, 'Wart. ost.', convert_float )
    apply_on_column( dataFrame, 'Wartość obrotu skum. (w tys. zł)', convert_float )

    apply_on_column( dataFrame, 'Liczba spółek', convert_int )
    apply_on_column( dataFrame, '% otw. portfela', convert_int )


def append_stock_isin( dataFrame, dataFile ):
    with open(dataFile, 'r') as file:
        fileContent = file.read()

    isinList = []

    for name in dataFrame["Nazwa"]:
        # pylint: disable=W1401
        pattern = r'<a\s*href="spolka\?isin=(\S*?)">' + name + r'.*?</a>'
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

    dataFrame["isin"] = isinList


def append_indexes_isin( dataFrame, dataFile ):
    with open(dataFile, 'r') as file:
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

    dataFrame["isin"] = isinList
