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

import pandas
from pandas.core.frame import DataFrame

from stockmonitor.dataaccess import tmp_dir
from stockmonitor.dataaccess.convert import convert_float, convert_int, cleanup_column, apply_on_column
from stockmonitor.dataaccess.worksheetdata import WorksheetData


_LOGGER = logging.getLogger(__name__)


## https://www.gpw.pl/wskazniki
class GpwIndicatorsData( WorksheetData ):

    def getStockIsin(self, rowIndex):
        dataFrame = self.getWorksheet()
        tickerColumn = dataFrame["Kod"]
        return tickerColumn.iloc[ rowIndex ]

    def parseDataFromFile(self, dataFile: str) -> DataFrame:
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

    def getDataPath(self):
        return tmp_dir + "data/gpw/indicators_data.html"

    def getDataUrl(self):
        return "https://www.gpw.pl/wskazniki"

    def sourceLink(self):
        return self.getDataUrl()


## ==========================================================================


## http://infostrefa.com/infostrefa/pl/spolki
class GpwIsinMapData( WorksheetData ):

    def getTickerFromIsin(self, stockIsin):
        dataFrame = self.getWorksheet()
        rowIndexes = dataFrame[ dataFrame["ISIN"] == stockIsin ].index.values
        if not rowIndexes:
            return None
        rowIndex = rowIndexes[0]
        tickerColumn = dataFrame["Ticker"]
        return tickerColumn.iloc[ rowIndex ]

    def getTickerFromName(self, stockName):
        dataFrame = self.getWorksheet()
        rowIndexes = dataFrame[ dataFrame["Nazwa giełdowa"] == stockName ].index.values
        if not rowIndexes:
            return None
        rowIndex = rowIndexes[0]
        tickerColumn = dataFrame["Ticker"]
        return tickerColumn.iloc[ rowIndex ]

    def getStockIsinFromTicker(self, ticker):
        dataFrame = self.getWorksheet()
        rowIndexes = dataFrame[ dataFrame["Ticker"] == ticker ].index.values
        if not rowIndexes:
            _LOGGER.warning("no isin found for ticker %s", ticker)
            return None
        rowIndex = rowIndexes[0]
        tickerColumn = dataFrame["ISIN"]
        return tickerColumn.iloc[ rowIndex ]

    def getNameFromTicker(self, ticker):
        dataFrame = self.getWorksheet()
        rowIndexes = dataFrame[ dataFrame["Ticker"] == ticker ].index.values
        if not rowIndexes:
            return None
        rowIndex = rowIndexes[0]
        tickerColumn = dataFrame["Emitent"]
        return tickerColumn.iloc[ rowIndex ]

    def parseDataFromFile(self, dataFile: str) -> DataFrame:
        _LOGGER.debug( "opening workbook: %s", dataFile )
        allDataFrames = pandas.read_html( dataFile, thousands='', decimal=',', encoding='utf-8' )
        dataFrame = allDataFrames[1]
        return dataFrame

    def getDataPath(self):
        return tmp_dir + "data/gpw/isin_map_data.html"

    def getDataUrl(self):
        ## this source does not seem to be viable,
        ## because it lacks a lot of tickers/isin values
        return "http://infostrefa.com/infostrefa/pl/spolki"
