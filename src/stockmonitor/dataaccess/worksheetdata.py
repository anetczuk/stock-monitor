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
import ssl

from pandas.core.frame import DataFrame

from stockmonitor import persist
from stockmonitor.synchronized import synchronized


_LOGGER = logging.getLogger(__name__)


def download_html_content( url, outputPath ):
    try:
        ##
        ## Under Ubuntu 20 SSL configuration has changed causing problems with SSL keys.
        ## For more details see: https://forums.raspberrypi.com/viewtopic.php?t=255167
        ##
        ctx_no_secure = ssl.create_default_context()
        ctx_no_secure.set_ciphers('HIGH:!DH:!aNULL')
        ctx_no_secure.check_hostname = False
        ctx_no_secure.verify_mode = ssl.CERT_NONE
    
        result = urllib.request.urlopen( url, context=ctx_no_secure )
        content_data = result.read()
        content_text = content_data.decode("utf-8") 
        
        with open(outputPath, 'wt') as of:
            of.write( content_text )
        
#         urllib.request.urlretrieve( url, outputPath, context=ctx_no_secure )
    except urllib.error.HTTPError:
        _LOGGER.exception( "exception when accessing: %s", url )
        raise
    except urllib.error.URLError as ex:
        _LOGGER.exception( "unable to access: %s %s", url, ex, exc_info=False )
        raise
    except ConnectionResetError as ex:
        _LOGGER.exception( "unable to access -- connection reset: %s %s", url, ex, exc_info=False )
        raise


class BaseWorksheetData( metaclass=abc.ABCMeta ):

    def __init__(self):
        self.worksheet: DataFrame = None

    @synchronized
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

    @synchronized
    def loadWorksheet(self, forceRefresh=False):
        dataPath = self.getDataPath()
        if forceRefresh is False:
            forceRefresh = not os.path.exists( dataPath )
        if forceRefresh:
            try:
                self.downloadData()
            except urllib.error.HTTPError:
                self.worksheet     = None
                self.grabTimestamp = None
            except urllib.error.URLError:
                self.worksheet     = None
                self.grabTimestamp = None

        if not os.path.exists( dataPath ):
            _LOGGER.warning( "could not find required file[%s]", dataPath )
            return

        _LOGGER.debug( "loading recent data from file[%s], force: %s", dataPath, forceRefresh )
        try:
            self._loadObjectData( forceRefresh )
        except BaseException:
            _LOGGER.exception( "unable to load object data" )
            return
        
        if self.worksheet is None:
            self.grabTimestamp = None
            return

        timestampPath = self.getTimestampPath()
        if not os.path.exists( timestampPath ):
            self.grabTimestamp = None
            return
        self.grabTimestamp = persist.load_object_simple( timestampPath, None )

    def _loadObjectData(self, forceRefresh=False):
        picklePath = self.getPicklePath()
        if forceRefresh is False:
            forceRefresh = not os.path.exists( picklePath )
        if forceRefresh is False:
            try:
                self.worksheet = persist.load_object_simple( picklePath, None )
                if self.worksheet is not None:
                    return
            except ModuleNotFoundError:
                ## this might happen when object files are shared between
                ## different operating systems (different versions of libraries)
                _LOGGER.exception( "unable to load object data files[%s], continuing with raw data file", picklePath, exc_info=False )
            except AttributeError:
                ## this might happen when module updated between save and load
                ## e.g.: AttributeError: Can't get attribute 'new_block' on <module 'pandas.core.internals.blocks' from 'site-packages/pandas/core/internals/blocks.py'>
                _LOGGER.exception( "unable to load object data files[%s], continuing with raw data file", picklePath, exc_info=False )

        self.parseDataFromDefaultFile()
        if self.worksheet is not None:
            persist.store_object_simple(self.worksheet, picklePath)

    def downloadData(self):
        filePath = self.getDataPath()
        self._downloadDataTo( filePath )

    def _downloadDataTo( self, filePath ):
        url = self.getDataUrl()
        _LOGGER.debug( "grabbing data from url[%s] to file[%s]", url, filePath )

        dirPath = os.path.dirname( filePath )
        os.makedirs( dirPath, exist_ok=True )

        currTimestamp = datetime.datetime.today()
        self._downloadContent( url, filePath )

        timestampPath = self.getTimestampPath()
        persist.store_object_simple(currTimestamp, timestampPath)

    def _downloadContent( self, url, filePath ):
        download_html_content( url, filePath )

    def parseDataFromDefaultFile(self):
        dataPath = self.getDataPath()
        _LOGGER.info( "parsing raw data: %s", dataPath )
        self.parseWorksheetFromFile( dataPath )

    @synchronized
    def parseWorksheetFromFile(self, dataPath: str):
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
