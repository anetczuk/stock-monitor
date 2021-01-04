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

from typing import List

import re
import pandas
from pandas.core.frame import DataFrame

from stockmonitor.dataaccess import tmp_dir
from stockmonitor.dataaccess.datatype import CurrentDataType
from stockmonitor.dataaccess.worksheetdata import WorksheetData,\
    BaseWorksheetData
from stockmonitor.dataaccess.convert import apply_on_column, convert_float,\
    convert_int, cleanup_column
from stockmonitor.synchronized import synchronized


_LOGGER = logging.getLogger(__name__)


class GpwCurrentStockData( WorksheetData ):
    """Handle GPW current day data."""

    def getStockData(self, tickerList: List[str] = None) -> DataFrame:
        if tickerList is None:
            return None
        dataFrame = self.getWorksheet()
        if dataFrame is None:
            return None
        colIndex = self.getColumnIndex( CurrentDataType.TICKER )
        retRows = dataFrame.loc[ dataFrame.iloc[:, colIndex].isin( tickerList ) ]
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
        colIndex = self.getColumnIndex( CurrentDataType.TICKER )
        retRows = dataFrame.loc[ dataFrame.iloc[:, colIndex] == ticker ]
        return retRows.squeeze()            ## convert 1 row dataframe to series

    def getTickerField(self, rowIndex: int):
        dataFrame = self.getWorksheet()
        if dataFrame is None:
            return None
        return self.getTickerFieldFromData( dataFrame, rowIndex )

    def getTickerFromIsin(self, stockIsin):
        dataFrame = self.getWorksheet()
        rowIndexes = dataFrame[ dataFrame["isin"] == stockIsin ].index.values
        if rowIndexes is None or len(rowIndexes) < 1:
            return None
        rowIndex = rowIndexes[0]
        tickerColumn = dataFrame["Skrót"]
        return tickerColumn.iloc[ rowIndex ]

    def getTickerFromName(self, stockName):
        dataFrame = self.getWorksheet()
        rowIndexes = dataFrame[ dataFrame["Nazwa"] == stockName ].index.values
        if rowIndexes is None or len(rowIndexes) < 1:
            return None
        rowIndex = rowIndexes[0]
        tickerColumn = dataFrame["Skrót"]
        return tickerColumn.iloc[ rowIndex ]

    def getStockIsinFromTicker(self, ticker):
        dataFrame = self.getWorksheet()
        reducedFrame = dataFrame[ dataFrame["Skrót"] == ticker ]
        rowIndexes = reducedFrame.index.values
        if rowIndexes is None or len(rowIndexes) < 1:
            _LOGGER.warning("no isin found for ticker %s\n%s", ticker, dataFrame)
            return None
        rowIndex = rowIndexes[0]
        tickerColumn = dataFrame["isin"]
        return tickerColumn.iloc[ rowIndex ]

    def getNameFromTicker(self, ticker):
        dataFrame = self.getWorksheet()
        rowIndexes = dataFrame[ dataFrame["Skrót"] == ticker ].index.values
        if rowIndexes is None or len(rowIndexes) < 1:
            return None
        rowIndex = rowIndexes[0]
        tickerColumn = dataFrame["Nazwa"]
        return tickerColumn.iloc[ rowIndex ]

    def getTickerFieldByName(self, stockName):
        dataFrame = self.getWorksheet()
        if dataFrame is None:
            return None
        nameIndex = self.getColumnIndex( CurrentDataType.NAME )
        tickerIndex = self.getColumnIndex( CurrentDataType.TICKER )
        retRows = dataFrame.loc[ dataFrame.iloc[:, nameIndex] == stockName ]
        if retRows.shape[0] > 0:
            return retRows.iloc[0, tickerIndex]
        return None

    def getTickerFieldFromData(self, dataFrame: DataFrame, rowIndex: int):
        colIndex = self.getColumnIndex( CurrentDataType.TICKER )
        if colIndex is None:
            return None
        return dataFrame.iloc[rowIndex, colIndex]

    def getRecentValue(self, ticker):
        row = self.getRowByTicker( ticker )
        return row.iloc[11]

    def getRecentChange(self, ticker):
        row = self.getRowByTicker( ticker )
        return row.iloc[12]

    def getReferenceValue(self, ticker):
        row = self.getRowByTicker( ticker )
        return row.iloc[6]

    # ==========================================================================

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

    def getGoogleLinkFromTicker(self, ticker):
        infoLink = "https://www.google.com/search?q=spolka+gpw+%s" % ticker
        return infoLink

    def getMoneyLinkFromIsin(self, isin):
        return "https://www.money.pl/gielda/spolki-gpw/%s.html" % isin

    ## ======================================================================

    def parseDataFromFile(self, dataFile: str) -> DataFrame:
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

    def getDataPath(self):
        return tmp_dir + "data/gpw/recent_data.xls"

    def getDataUrl(self):
        url = ("https://www.gpw.pl/ajaxindex.php"
               "?action=GPWQuotations&start=showTable&tab=all&lang=PL&full=1&format=html&download_xls=1")
        return url

    def sourceLink(self):
        return "https://www.gpw.pl/akcje"

    @staticmethod
    def getColumnIndex(dataType: CurrentDataType):
        switcher = {
            CurrentDataType.NAME:               2,
            CurrentDataType.TICKER:             3,
            CurrentDataType.CURRENCY:           4,
            CurrentDataType.RECENT_TRANS_TIME:  5,
            CurrentDataType.REFERENCE:          6,
            CurrentDataType.TKO:                7,
            CurrentDataType.OPENING:            8,
            CurrentDataType.MIN:                9,
            CurrentDataType.MAX:               10,
            CurrentDataType.RECENT_TRANS:      11
        }
        return switcher.get(dataType, None)

    @staticmethod
    def unitPrice( dataRow ):
        ## current value
        currUnitValueIndex = GpwCurrentStockData.getColumnIndex( CurrentDataType.RECENT_TRANS )
        currUnitValueRaw = dataRow.iloc[currUnitValueIndex]
        if currUnitValueRaw != "-":
            return float( currUnitValueRaw )

        ## TKO
#        tkoIndex = GpwCurrentStockData.getColumnIndex( CurrentDataType.TKO )
#        tkoValueRaw = dataRow.iloc[tkoIndex]
#        if tkoValueRaw != "-":
#            return float( tkoValueRaw )

        ## reference value
        refValueIndex = GpwCurrentStockData.getColumnIndex( CurrentDataType.REFERENCE )
        refValueRaw = dataRow.iloc[refValueIndex]
        if refValueRaw != "-":
            return float( refValueRaw )

        return 0.0


# ============================================================================


class GpwCurrentIndexesData( BaseWorksheetData ):

    def __init__(self):
        super().__init__()
        self.dataList = list()
        self.dataList.append( GpwMainIndexesData() )
        self.dataList.append( GpwMacroIndexesData() )
        self.dataList.append( GpwSectorsIndexesData() )

    def getNameFromIsin(self, isin):
        row = self.getRowByIsin( isin )
        return row.iloc[1]

    def getRecentValue(self, isin):
        row = self.getRowByIsin( isin )
        return row.iloc[8]

    def getRecentChange(self, isin):
        row = self.getRowByIsin( isin )
        return row.iloc[9]

    def getRowByIsin(self, isin):
        dataFrame = self.getWorksheet()
        if dataFrame is None:
            _LOGGER.warning("no worksheet found")
            return None
        isinColumn = dataFrame.iloc[:, 12]
        retRows = dataFrame.loc[ isinColumn == isin ]
        return retRows.squeeze()            ## convert 1 row dataframe to series

    @synchronized
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


class GpwMainIndexesData( WorksheetData ):

    def parseDataFromFile(self, dataFile: str) -> DataFrame:
        _LOGGER.debug( "opening workbook: %s", dataFile )
        allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
        dataFrame = DataFrame()
        dataFrame = dataFrame.append( allDataFrames[0] )        ## realtime indexes
        dataFrame = dataFrame.append( allDataFrames[1] )        ## main indexes
        convert_indexes_data( dataFrame )
        append_indexes_isin( dataFrame, dataFile )
        return dataFrame

    def getDataPath(self):
        return tmp_dir + "data/gpw/indexes_main_data.html"

    def getDataUrl(self):
        url = "https://gpwbenchmark.pl/ajaxindex.php?action=GPWIndexes&start=showTable&tab=indexes&lang=PL"
        return url


class GpwMacroIndexesData( WorksheetData ):

    def parseDataFromFile(self, dataFile: str) -> DataFrame:
        _LOGGER.debug( "opening workbook: %s", dataFile )
        allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
        dataFrame = allDataFrames[0]
        convert_indexes_data( dataFrame )
        append_indexes_isin( dataFrame, dataFile )
        return dataFrame

    def getDataPath(self):
        return tmp_dir + "data/gpw/indexes_macro_data.html"

    def getDataUrl(self):
        url = "https://gpwbenchmark.pl/ajaxindex.php?action=GPWIndexes&start=showTable&tab=macroindices&lang=PL"
        return url


class GpwSectorsIndexesData( WorksheetData ):

    def parseDataFromFile(self, dataFile: str) -> DataFrame:
        _LOGGER.debug( "opening workbook: %s", dataFile )
        allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
        dataFrame = allDataFrames[0]
        convert_indexes_data( dataFrame )
        append_indexes_isin( dataFrame, dataFile )
        return dataFrame

    def getDataPath(self):
        return tmp_dir + "data/gpw/indexes_sectors_data.html"

    def getDataUrl(self):
        return "https://gpwbenchmark.pl/ajaxindex.php?action=GPWIndexes&start=showTable&tab=sectorbased&lang=PL"


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
        pattern = '<a\s*href="spolka\?isin=(\S*?)">' + name + '.*?</a>'
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
        pattern = '<a href="/karta-indeksu\?isin=(\S*?)">' + short + '</a>'
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
