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
import pandas
from pandas.core.frame import DataFrame

from stockmonitor.dataaccess import tmp_dir
from stockmonitor.dataaccess.worksheetdata import WorksheetData


_LOGGER = logging.getLogger(__name__)


## https://www.stockwatch.pl/dywidendy/
class DividendsCalendarData( WorksheetData ):

    def getStockName(self, rowIndex):
        dataFrame = self.getWorksheet()
        tickerColumn = dataFrame["Spółka"]
        return tickerColumn.iloc[ rowIndex ]

    def getLawDate(self, rowIndex):
        dataFrame = self.getWorksheet()
        dateColumn = dataFrame["Notowanie bez dyw."]
        dateString = dateColumn.iloc[ rowIndex ]
        try:
            dateObject = datetime.datetime.strptime(dateString, '%Y-%m-%d').date()
            return dateObject
        except ValueError:
            return datetime.date( 1, 1, 1 )

    def parseDataFromFile(self, dataFile) -> DataFrame:
        _LOGGER.debug( "opening workbook: %s", dataFile )
        dataFrame = pandas.read_html( dataFile, thousands='', decimal=',' )
        dataFrame = dataFrame[2]
        dataFrame = dataFrame.fillna("-")
        return dataFrame

    def getDataPath(self):
        return tmp_dir + "data/stockwatch/dividends_cal_data.html"

    def getDataUrl(self):
        url = "https://www.stockwatch.pl/dywidendy/"
        return url

    def sourceLink(self):
        return self.getDataUrl()
