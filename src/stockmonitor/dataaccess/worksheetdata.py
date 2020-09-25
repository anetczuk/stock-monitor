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
import abc
import urllib

from pandas.core.frame import DataFrame

from stockmonitor import persist


_LOGGER = logging.getLogger(__name__)


def download_content( url, outputPath ):
    try:
        dirPath = os.path.dirname( outputPath )
        os.makedirs( dirPath, exist_ok=True )
        urllib.request.urlretrieve( url, outputPath )
    except urllib.error.HTTPError:
        _LOGGER.exception( "exception when accessing: %s", url )
        raise


class BaseWorksheetData( metaclass=abc.ABCMeta ):

    def __init__(self):
        self.worksheet: DataFrame = None

    def getWorksheet(self, forceRefresh=False) -> DataFrame:
        if self.worksheet is None or forceRefresh is True:
#             _LOGGER.info("state: %s %s", (self.worksheet is None), (forceRefresh is True) )
            self.refreshData( forceRefresh )
        return self.worksheet

    def refreshData(self, forceRefresh=True):
        self.loadWorksheet( forceRefresh )

    @abc.abstractmethod
    def loadWorksheet(self, forceRefresh=False):
        raise NotImplementedError('You need to define this method in derived class!')


class WorksheetData( BaseWorksheetData ):

    def __init__(self):
        super().__init__()
        self.grabTimestamp: datetime.datetime = None

    def loadWorksheet(self, forceRefresh=False):
        dataPath = self.getDataPath()
        if forceRefresh is False:
            forceRefresh = not os.path.exists( dataPath )
        if forceRefresh:
            self.downloadData()

        if not os.path.exists( dataPath ):
            _LOGGER.warning( "could not find required file[%s]", dataPath )
            return

        _LOGGER.debug( "loading recent data from file[%s], force: %s", dataPath, forceRefresh )
        self.loadObjectData( forceRefresh )
        if self.worksheet is None:
            self.grabTimestamp = None
            return

        timestampPath = self.getTimestampPath()
        if not os.path.exists( timestampPath ):
            self.grabTimestamp = None
            return
        self.grabTimestamp = persist.load_object_simple( timestampPath, None )

    def loadObjectData(self, forceRefresh=False):
        picklePath = self.getPicklePath()
        if forceRefresh is False:
            forceRefresh = not os.path.exists( picklePath )
        if forceRefresh is False:
            try:
                self.worksheet = persist.load_object_simple( picklePath, None )
                if self.worksheet is not None:
                    return
            except ModuleNotFoundError:
                ## ths might happen when object files are shared between
                ## different operating systems (different versions of libraries)
                _LOGGER.exception( "unable to load object data files[%s], continuing with raw data file", picklePath )

        self.parseDataFromDefaultFile()
        if self.worksheet is not None:
            persist.store_object_simple(self.worksheet, picklePath)

    def downloadData(self):
        filePath = self.getDataPath()

        url = self.getDataUrl()
        _LOGGER.debug( "grabbing data from url[%s] to file[%s]", url, filePath )

        currTimestamp = datetime.datetime.today()
        download_content( url, filePath )

        timestampPath = self.getTimestampPath()
        persist.store_object_simple(currTimestamp, timestampPath)

    def parseDataFromDefaultFile(self):
        dataPath = self.getDataPath()
        _LOGGER.info( "parsing raw data: %s", dataPath )
        self.worksheet = self.parseDataFromFile( dataPath )

    def getPicklePath(self):
        dataPath = self.getDataPath()
        return dataPath + ".pickle"

    def getTimestampPath(self):
        dataPath = self.getDataPath()
        return dataPath + ".timestamp"

    @abc.abstractmethod
    def parseDataFromFile(self, dataFile: str) -> DataFrame:
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def getDataPath(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def getDataUrl(self):
        raise NotImplementedError('You need to define this method in derived class!')


## ================================================================================


class WorksheetDataMock( BaseWorksheetData ):

    def __init__(self, data=None):
        super().__init__()
        self.worksheet = data

    def loadWorksheet(self, _=False):
        pass


# class HtmlWorksheetData( WorksheetData ):
#
#     def parseDataFromFile(self, dataFile: str) -> DataFrame:
#         _LOGGER.debug( "opening workbook: %s", dataFile )
#         dataFrame = pandas.read_html( dataFile )
#         dataFrame = dataFrame[0]
#         return dataFrame
