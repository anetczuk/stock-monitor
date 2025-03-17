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

import unittest
import logging
import datetime

from teststockdataaccess.data import get_data_path

from stockdataaccess.dataaccess.gpw.gpwintradaydata import GpwCurrentStockIntradayData
from stockdataaccess.dataaccess.metastockdata import MetaStockIntradayData
from stockdataaccess.dataaccess.worksheetdata import WorksheetStorageMock
from stockmonitor.analysis.activityanalysis import GpwCurrentIntradayProvider, \
    ActivityAnalysis, MetaStockIntradayProvider


_LOGGER = logging.getLogger(__name__)


## =================================================================


class GpwCurrentIntradayProviderMock( GpwCurrentIntradayProvider ):

    def _loadData(self, isin):
#         name, isin   = paramsList
        intradayData = GpwCurrentStockIntradayData( "PLOPTTC00011" )

        def data_path():
            return get_data_path( "cdr.chart.04-09.txt" )

        intradayData.dao.getDataPath = data_path           # type: ignore
        intradayData.dao.storage = WorksheetStorageMock()
        worksheet = intradayData.dao.parseWorksheetFromFile( data_path() )
        return worksheet


class MetaStockIntradayProviderMock( MetaStockIntradayProvider ):

    ## override
    def _loadData(self):
        dataAccess = MetaStockIntradayData()

        def data_path():
            return get_data_path( "a_cgl_intraday_2020-08-17.prn" )

        dataAccess.dao.getDataPath = data_path                      # type: ignore
        dataAccess.dao.downloadData = lambda filePath: None         ## empty lambda function
        dataAccess.dao.storage = WorksheetStorageMock()
        return dataAccess.getWorksheetData( True )


class ActivityAnalysisMock( ActivityAnalysis ):

    def getPrecalcData(self, currDate):
        _LOGGER.debug( "loading data for: %s", currDate )
        dataPair = self.precalculateData( currDate )
        return list( dataPair ) + [ currDate ]

    def getISINForDate( self, toDay ):
        return { "CDPROJEKT": "PLOPTTC00011" }


## =================================================================


class ActivityAnalysisTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_calc_current(self):
        dataProvider = GpwCurrentIntradayProviderMock()
        analysis = ActivityAnalysisMock( dataProvider )
        today = datetime.datetime.now().date()
        results = analysis.calcActivity( today, today, 2.0 )
        self.assertEqual( results.shape[0], 1 )
        row = results.iloc[0]
        self.assertEqual( row["name"], "CDPROJEKT" )
        self.assertEqual( row["relative"], 0.3251 )
        self.assertEqual( row["price activity"], 4 )
        self.assertEqual( row["price change sum"], 2.3499 )
        self.assertEqual( row["price change deviation"], 224.8795 )

    def test_calc_previous(self):
        dataProvider = MetaStockIntradayProviderMock()
        analysis = ActivityAnalysisMock( dataProvider )
        today = datetime.date( year=2020, month=9, day=1 )
        results = analysis.calcActivity( today, today, 2.0 )
        self.assertEqual( results.shape[0], 1 )
        row = results.iloc[0]
        self.assertEqual( row["name"], "CDPROJEKT" )
        self.assertEqual( row["relative"], 0.9211 )
        self.assertEqual( row["price activity"], 0 )
        self.assertEqual( row["price change sum"], -0.6337 )
        self.assertEqual( row["price change deviation"], 82.3829 )
