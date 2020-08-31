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
    dirPath = os.path.dirname( outputPath )
    os.makedirs( dirPath, exist_ok=True )
    urllib.request.urlretrieve( url, outputPath )


class BaseWorksheetData( metaclass=abc.ABCMeta ):

    def __init__(self):
        self.worksheet: DataFrame = None

    def refreshData(self, forceRefresh=True):
        self.loadWorksheet( forceRefresh )

    def getWorksheet(self, forceRefresh=False) -> DataFrame:
        if self.worksheet is None or forceRefresh is True:
            self.loadWorksheet( forceRefresh )
        return self.worksheet

    @abc.abstractmethod
    def loadWorksheet(self, forceRefresh=False):
        raise NotImplementedError('You need to define this method in derived class!')


class WorksheetData( BaseWorksheetData ):

    def __init__(self):
        super().__init__()
        self.grabTimestamp: datetime.datetime = None

    def loadWorksheet(self, forceRefresh=False):
        dataPath, timestampPath = self.getDataPaths()
        if forceRefresh is True or not os.path.exists( dataPath ):
            self.downloadData()

        if not os.path.exists( dataPath ):
            return

        _LOGGER.debug( "loading recent data from file[%s]", dataPath )
        self.worksheet = self.loadWorksheetFromFile( dataPath )

        if timestampPath is None:
            self.grabTimestamp = None
            return
        if not os.path.exists( timestampPath ):
            self.grabTimestamp = None
            return
        self.grabTimestamp = persist.load_object_simple( timestampPath, None )

    def downloadData(self):
        filePath, timestampPath = self.getDataPaths()

        url = self.getDataUrl()
        _LOGGER.debug( "grabbing data from url[%s] to file[%s]", url, filePath )

        currTimestamp = datetime.datetime.today()
        download_content( url, filePath )
        if timestampPath is not None:
            persist.store_object_simple(currTimestamp, timestampPath)

    @abc.abstractmethod
    def loadWorksheetFromFile(self, dataFile: str) -> DataFrame:
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def getDataPaths(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def getDataUrl(self):
        raise NotImplementedError('You need to define this method in derived class!')


# class HtmlWorksheetData( WorksheetData ):
#
#     def loadWorksheetFromFile(self, dataFile: str) -> DataFrame:
#         _LOGGER.debug( "opening workbook: %s", dataFile )
#         dataFrame = pandas.read_html( dataFile )
#         dataFrame = dataFrame[0]
#         return dataFrame
