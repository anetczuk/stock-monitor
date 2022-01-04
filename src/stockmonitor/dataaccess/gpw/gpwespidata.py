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
import re

import pandas
from pandas.core.frame import DataFrame
from bs4 import BeautifulSoup

from stockmonitor.dataaccess import tmp_dir
from stockmonitor.dataaccess.worksheetdata import WorksheetData, BaseWorksheetDAO
from stockmonitor.synchronized import synchronized


_LOGGER = logging.getLogger(__name__)


## https://www.gpw.pl/komunikaty
class GpwESPIData( BaseWorksheetDAO ):

    class DAO( WorksheetData ):
        """Data access object."""
        
        def __init__(self):
            super().__init__()
            self.messagesLimit = 30
        
        def getDataPath(self):
            return tmp_dir + "data/gpw/espi_data.html"
    
        def getDataUrl(self):
            offset = 0
            url = "https://www.gpw.pl/ajaxindex.php" \
                  "?action=GPWEspiReportUnion&start=ajaxSearch&page=komunikaty&format=html&lang=PL&letter=" \
                  "&offset=" + str(offset) + \
                  "&limit="  + str(self.messagesLimit) + \
                  "&categoryRaports%5B%5D=EBI&categoryRaports%5B%5D=ESPI" \
                  "&typeRaports%5B%5D=RB&typeRaports%5B%5D=P&typeRaports%5B%5D=Q&typeRaports%5B%5D=O&typeRaports%5B%5D=R" \
                  "&search-xs=&searchText=&date="
            return url
    #         return "https://www.gpw.pl/komunikaty"
    
        @synchronized
        def _parseDataFromFile(self, dataFile: str) -> DataFrame:
#             _LOGGER.debug( "opening workbook: %s", dataFile )
    
            with open( dataFile ) as file:
                soup = BeautifulSoup(file, "html.parser")
                data_dicts = []
                for row in soup.select('li'):
                    if row is None:
                        continue
                    dateRow    = row.select('span.date')
                    dateRaw    = dateRow[0].string
                    dateString = dateRaw.split('|')[0].strip()
                    dateObj    = datetime.datetime.strptime(dateString, '%d-%m-%Y %H:%M:%S')          ## 23-10-2020 23:09:01
    
                    nameRow = row.select('strong.name')[0]
                    name    = nameRow.a.string.strip()
    
                    isinRes = re.search( r"\((.+)\)", name )
                    isin    = None
                    if isinRes is not None:
                        isin = isinRes.groups()[0]
    
                    title = row.p.string.strip()
    
                    url = "https://www.gpw.pl/" + row.a['href']
    
                    row_dict = {}
                    row_dict["name"]  = name
                    row_dict["isin"]  = isin
                    row_dict["date"]  = dateObj
                    row_dict["title"] = title
                    row_dict["url"]   = url
    
                    data_dicts.append(row_dict)
    
                dataFrame = pandas.DataFrame(data_dicts)
    
                return dataFrame


    def __init__(self):
        dao = GpwESPIData.DAO()
        super().__init__( dao )

    def sourceLink(self):
        return "https://www.gpw.pl/komunikaty"

    def setLimit(self, number):
        self.dao.messagesLimit = number
