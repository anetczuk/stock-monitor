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
from typing import List

import datetime
import abc

from pandas.core.frame import DataFrame

from stockmonitor import persist
from stockmonitor.synchronized import synchronized
from stockmonitor.dataaccess.datatype import StockDataType


_LOGGER = logging.getLogger(__name__)


## ==============================================================================


class BaseWorksheetData( metaclass=abc.ABCMeta ):

    ## get data
    @synchronized
    def getWorksheetData(self, forceRefresh=False) -> DataFrame:
        if forceRefresh is True:
            self.loadWorksheet()
        return self.getDataFrame()

    ## get data, if data is None then try to load it before returning
    @synchronized
    def accessWorksheetData(self, forceRefresh=False) -> DataFrame:
        if forceRefresh is True:
            self.loadWorksheet()
            return self.getDataFrame()
        dataFrame = self.getDataFrame()
        if dataFrame is None:
            self.loadWorksheet()
        return self.getDataFrame()

    ## load data to internal buffer (include downloading and parsing raw data)
    ## return loaded data
    @abc.abstractmethod
    def loadWorksheet(self, preventDownload=False):
        raise NotImplementedError('You need to define this method in derived class!')

    ## get current data (without scraping -- loading from local cache allowed)
    @abc.abstractmethod
    def getDataFrame(self) -> DataFrame:
        raise NotImplementedError('You need to define this method in derived class!')


##
##
class WorksheetData( BaseWorksheetData ):

    def __init__(self):
        super().__init__()
        self.storage = WorksheetStorage()

    def getGrabTimestmp(self) -> datetime.datetime:
        return self.storage.grabTimestamp

    ## override
    @synchronized
    def loadWorksheet(self, preventDownload=False):
        try:
            ## forced refresh or no data -- download new data
            dataPath = self.getDataPath()

            ## ensure output directory exists
            dirPath = os.path.dirname( dataPath )
            os.makedirs( dirPath, exist_ok=True )

            #preventDownload
            if preventDownload is False or os.path.exists( dataPath ) is False:
                self.downloadData( dataPath )
            return self.parseWorksheetFromFile( dataPath )

        except BaseException:
            self.storage.clear()

        return None

    @abc.abstractmethod
    def downloadData(self, filePath):
        raise NotImplementedError('You need to define this method in derived class!')

    def parseWorksheetFromFile(self, dataPath: str):
        # _LOGGER.info( "parsing raw data: %s", dataPath )
        worksheet = self._parseDataFromFile( dataPath )
        self.storage.storeObject( dataPath, worksheet )
        return worksheet

    ## ====================================================

    ## override
    def getDataFrame(self) -> DataFrame:
        if self.storage.worksheet is None:
            dataPath = self.getDataPath()
            self.storage.loadObject( dataPath, False )
        return self.storage.worksheet

    ## return None if no data found
    @abc.abstractmethod
    def _parseDataFromFile(self, dataFile: str) -> DataFrame:
        raise NotImplementedError('You need to define this method in derived class!')

    ## path can be generated dynamically
    @abc.abstractmethod
    def getDataPath(self):
        raise NotImplementedError('You need to define this method in derived class!')


##
##
class WorksheetStorage():
    """Store and load data."""

    def __init__(self):
        self.worksheet: DataFrame = None
        self.grabTimestamp: datetime.datetime = None

    def clear(self):
        self.worksheet = None
        self.grabTimestamp = None

    def loadObject(self, dataPath, forceRefresh=False):
        if forceRefresh is False and self.worksheet is not None:
            return self.worksheet

        try:
            picklePath = dataPath + ".pickle"
            self.worksheet = persist.load_object_simple( picklePath, None )
            if self.worksheet is None:
                self.clear()
                return self.worksheet

            timestampPath = dataPath + ".timestamp"
            self.grabTimestamp = persist.load_object_simple( timestampPath, None )
            if self.grabTimestamp is None:
                self.grabTimestamp = datetime.datetime.today()
            return self.worksheet
        except ModuleNotFoundError:
            ## this might happen when object files are shared between
            ## different operating systems (different versions of libraries)
            _LOGGER.exception( "unable to load object data files[%s], continuing with raw data file",
                               picklePath, exc_info=False )
        except AttributeError:
            ## this might happen when module updated between save and load
            ## e.g.: AttributeError: Can't get attribute 'new_block' on
            ## <module 'pandas.core.internals.blocks' from 'site-packages/pandas/core/internals/blocks.py'>
            _LOGGER.exception( "unable to load object data files[%s], continuing with raw data file",
                               picklePath, exc_info=False )
        except EOFError:
            _LOGGER.exception( "unable to load object data files[%s], continuing with raw data file",
                               picklePath, exc_info=False )

        self.clear()
        return None

    def storeObject(self, dataPath, objectToStore):
        self.worksheet = objectToStore
        if objectToStore is None:
            self.grabTimestamp = None
            return
        picklePath = dataPath + ".pickle"
        persist.store_object_simple( objectToStore, picklePath )

        self.grabTimestamp = datetime.datetime.today()
        timestampPath = dataPath + ".timestamp"
        persist.store_object_simple( self.grabTimestamp, timestampPath )


##
##
class WorksheetStorageMock():
    """Storage mock. Does not persist cached values."""

    def __init__(self):
        self.worksheet: DataFrame = None
        self.grabTimestamp: datetime.datetime = None

    def clear(self):
        self.worksheet = None
        self.grabTimestamp = None

    # def loadObject(self, dataPath, forceRefresh=False):
    def loadObject(self, _1, _2=False):
        return self.worksheet

    # def storeObject(self, dataPath, objectToStore):
    def storeObject(self, _, objectToStore):
        ## do nothing
        self.worksheet = objectToStore


## ================================================================================


class WorksheetDataMock( BaseWorksheetData ):

    def __init__(self, data=None):
        super().__init__()
        self.worksheet = data

    ## override
    def loadWorksheet(self, preventDownload=False):
        return self.worksheet

    ## override
    def getDataFrame(self) -> DataFrame:
        return self.worksheet


## ================================================================================


class BaseWorksheetDAO():

    def __init__( self, dao ):
        # self.dao: BaseWorksheetData
        self.dao = dao

    ## get data without downloading it
    def getDataFrame(self) -> DataFrame:
        return self.dao.getDataFrame()

    ## get data without downloading it ('force' causes data to be downloaded)
    def getWorksheetData(self, forceRefresh=False) -> DataFrame:
        return self.dao.getWorksheetData( forceRefresh )

    ## download data in case of None
    def accessWorksheetData(self, forceRefresh=False) -> DataFrame:
        return self.dao.accessWorksheetData( forceRefresh )

    ## download and parse data to worksheet
    ## return loaded data
    def loadWorksheet(self, preventDownload=False):
        return self.dao.loadWorksheet( preventDownload )

    ## ====================================

    def getDataByIndex( self, columnType: StockDataType, rowIndex ):
        colIndex = self.getDataColumnIndex( columnType )
        dataFrame: DataFrame = self.getDataFrame()
        try:
            dataColumn = dataFrame.iloc[:, colIndex]
        except IndexError as ex:
            _LOGGER.error( "invalid access: %s in index %s while accessing %s", ex, colIndex, columnType )
            raise
        return dataColumn.iloc[ rowIndex ]

    def getRowByValue( self, rowColumnType: StockDataType, rowValue ):
        colIndex = self.getDataColumnIndex( rowColumnType )
        dataFrame: DataFrame = self.getDataFrame()
        if dataFrame is None:
            return None
        ## extract column and find row index by comparing with 'value', then return row by the index
        retRows = dataFrame.loc[ dataFrame.iloc[:, colIndex] == rowValue ]
        return retRows.squeeze()                                            ## convert 1 row dataframe to series

    # def getRowsByValueList( self, rowColumnType: StockDataType, rowValues: List[str] ):
    def getRowsByValueList( self, rowColumnType: StockDataType, rowValues: List[str] ):
        if rowValues is None:
            return None
        dataFrame = self.getWorksheetData()
        if dataFrame is None:
            return None
        colIndex = self.getDataColumnIndex( rowColumnType )
        retRows = dataFrame.loc[ dataFrame.iloc[:, colIndex].isin( rowValues ) ]
        return retRows

    def getDataByValue( self, rowColumnType: StockDataType, rowValue, dataType: StockDataType ):
        dataIndex = self.getDataColumnIndex( dataType )
        rowData = self.getRowByValue( rowColumnType, rowValue )
        if rowData is None or len(rowData) < 1:
            return None
        return rowData[ dataIndex ]

    ## get column index
    @abc.abstractmethod
    def getDataColumnIndex( self, columnType: StockDataType ) -> int:
        raise NotImplementedError('You need to define this method in derived class!')


# class HtmlWorksheetData( WorksheetData ):
#
#     def _parseDataFromFile(self, dataFile: str) -> DataFrame:
#         _LOGGER.debug( "opening workbook: %s", dataFile )
#         dataFrame = pandas.read_html( dataFile )
#         dataFrame = dataFrame[0]
#         return dataFrame
