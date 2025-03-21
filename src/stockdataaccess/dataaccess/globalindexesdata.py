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

from bs4 import BeautifulSoup

from stockdataaccess.dataaccess import TMP_DIR
from stockdataaccess.dataaccess.worksheetdata import WorksheetDAO, BaseWorksheetData
from stockdataaccess.dataaccess import download_html_content
from stockdataaccess.dataaccess.convert import convert_float, convert_percentage, \
    apply_on_column
from stockdataaccess.synchronized import synchronized
from stockdataaccess.pprint import fullname
from stockdataaccess.dataaccess.datatype import StockDataType


_LOGGER = logging.getLogger(__name__)


class GlobalIndexesData( BaseWorksheetData ):

    class GlobalIndexesDAO( WorksheetDAO ):
        """Data access object."""

        def getDataPath(self):
            return TMP_DIR + "data/bankier/global_indexes_data.html"

        def getDataUrl(self):
            return "https://www.bankier.pl/gielda/gieldy-swiatowe/indeksy"

        ## override
        def downloadData(self, filePath):
            url = self.getDataUrl()

            ## relPath = os.path.relpath( filePath )
            _LOGGER.debug( "grabbing data from url[%s] as file[%s]", url.split("?", maxsplit=1)[0], filePath )

            try:
                download_html_content( url, filePath )
            except BaseException as ex:
                _LOGGER.exception( "unable to load object data -- %s: %s", fullname(ex), ex, exc_info=False )
                raise

        @synchronized
        def _parseDataFromFile(self, dataFile) -> DataFrame:
#             _LOGGER.debug( "opening workbook: %s", dataFile )

            # fix HTML: handle multiple tbody inside single table
            with open( dataFile, encoding="utf-8" ) as file:
                soup = BeautifulSoup(file, "html.parser")
                for body in soup("tbody"):
                    body.unwrap()

                dataFrame = pandas.read_html( str(soup), flavor="bs4" )
                dataFrame = dataFrame[0]

                dataFrame.dropna( how='all', inplace=True )

                apply_on_column( dataFrame, 'Kurs AD', convert_float )
                apply_on_column( dataFrame, 'Zmiana AD', convert_float )
                apply_on_column( dataFrame, 'Zmianaprocentowa AD', convert_percentage )
                apply_on_column( dataFrame, 'Otwarcie AD', convert_float )
                apply_on_column( dataFrame, 'Max AD', convert_float )
                apply_on_column( dataFrame, 'Min AD', convert_float )

                return dataFrame

    ## ==========================================================

    def __init__(self):
        dao = GlobalIndexesData.GlobalIndexesDAO()
        super().__init__( dao )

    def sourceLink(self):
        return self.dao.getDataUrl()

    ## get column index
    ## override
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
        raise ValueError( f"Invalid value: {columnType}" )
