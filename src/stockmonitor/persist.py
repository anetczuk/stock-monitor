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

import os
import zipfile
import filecmp
import pickle

import abc


_LOGGER = logging.getLogger(__name__)


class RenamingUnpickler(pickle.Unpickler):

    def __init__(self, codeVersion, file):
        super().__init__( file )
        self.codeVersion = codeVersion

    def find_class(self, module, name):
        if module == 'stockmonitor.gui.datatypes':
            module = 'stockmonitor.datatypes.datatypes'
        if module == 'stockmonitor.gui.wallettypes':
            module = 'stockmonitor.datatypes.wallettypes'
        return super().find_class(module, name)


def load_object( inputFile, codeVersion, defaultValue=None ):
    try:
        _LOGGER.info( "loading data from: %s", inputFile )
        with open( inputFile, 'rb') as fp:
            unpickler = RenamingUnpickler(codeVersion, fp)
            return unpickler.load()
#             return pickle.load(fp)
    except FileNotFoundError:
        _LOGGER.exception("failed to load")
        return defaultValue
    except AttributeError:
        _LOGGER.exception("failed to load")
        return defaultValue
    except Exception:
        _LOGGER.exception("failed to load")
        raise


def store_object( inputObject, outputFile ):
    tmpFile = outputFile + "_tmp"
    store_object_simple( inputObject, tmpFile )

    if os.path.isfile( outputFile ) is False:
        ## output file does not exist -- rename file
        _LOGGER.info( "saving data to: %s", outputFile )
        os.rename( tmpFile, outputFile )
        return True

    if filecmp.cmp( tmpFile, outputFile ) is True:
        ## the same files -- remove tmp file
        _LOGGER.info("no new data to store in %s", outputFile)
        os.remove( tmpFile )
        return False

    _LOGGER.info( "saving data to: %s", outputFile )
    os.remove( outputFile )
    os.rename( tmpFile, outputFile )
    return True


def store_backup( inputObject, outputFile ):
    if store_object( inputObject, outputFile ) is False:
        return False
    ## backup data
    storedZipFile = outputFile + ".zip"
    backup_files( [outputFile], storedZipFile )
    return True


def load_object_simple( inputFile, defaultValue=None, silent=False ):
    try:
#         _LOGGER.info( "loading data from: %s", inputFile )
        with open( inputFile, 'rb') as fp:
            return pickle.load(fp)
    except AttributeError:
        if silent is False:
            _LOGGER.exception( "failed to load: %s", inputFile )
        return defaultValue
    except FileNotFoundError:
        if silent is False:
            _LOGGER.exception( "failed to load: %s", inputFile, exc_info=False )
        return defaultValue
    except ModuleNotFoundError:
        ## class moved to other module
        if silent is False:
            _LOGGER.exception( "failed to load: %s", inputFile )
        return defaultValue


def store_object_simple( inputObject, outputFile ):
    outdirDir = os.path.dirname( outputFile )
    if not os.path.exists(outdirDir):
        os.makedirs(outdirDir, exist_ok=True)

    with open(outputFile, 'wb') as fp:
        pickle.dump( inputObject, fp )


def backup_files( inputFiles, outputArchive ):
    ## create zip
    tmpZipFile = outputArchive + "_tmp"
    zipf = zipfile.ZipFile( tmpZipFile, 'w', zipfile.ZIP_DEFLATED )
    for file in inputFiles:
        zipEntry = os.path.basename( file )
        zipf.write( file, zipEntry )
    zipf.close()

    ## compare content
    storedZipFile = outputArchive
    if os.path.isfile( storedZipFile ) is False:
        ## output file does not exist -- rename file
        _LOGGER.info( "storing data to: %s", storedZipFile )
        os.rename( tmpZipFile, storedZipFile )
        return

    if filecmp.cmp( tmpZipFile, storedZipFile ) is True:
        ## the same files -- remove tmp file
        _LOGGER.info("no new data to backup")
        os.remove( tmpZipFile )
        return

    ## rename files
    counter = 1
    nextFile = "%s.%s" % (storedZipFile, counter)
    while os.path.isfile( nextFile ):
        counter += 1
        nextFile = "%s.%s" % (storedZipFile, counter)
    _LOGGER.info( "found backup slot: %s", nextFile )

    currFile = storedZipFile
    while counter > 1:
        currFile = "%s.%s" % (storedZipFile, counter - 1)
        os.rename( currFile, nextFile )
        nextFile = currFile
        counter -= 1

    os.rename( storedZipFile, nextFile )
    os.rename( tmpZipFile, storedZipFile )


def compare_files_bytes( file1Path, file2Path ):
    contentA = read_file_bytes( file1Path )
    contentB = read_file_bytes( file2Path )
    aSize = len( contentA )
    bSize = len( contentB )
    if aSize != bSize:
        _LOGGER.info( "files size differ: %s %s", aSize, bSize )
        return
    for i in range(aSize):
        if contentA[i] != contentB[i]:
            _LOGGER.info( "files differ at byte %s: %s %s", i, contentA[i], contentB[i] )


def print_file_content( filePath ):
    byteList = read_file_bytes( filePath )
    #return ''.join('{:02x} '.format(x) for x in byteList)
    bSize = len( byteList )
    for i in range(bSize):
        print( ''.join( '{:06d}: {:02x}'.format( i, byteList[i] ) ) )


def read_file_bytes( filePath ):
    byteList = []
    with open(filePath, 'rb') as f:
        while 1:
            byte_s = f.read(1)
            if not byte_s:
                break
            byteList.append( byte_s[0] )
    return byteList


## ==========================================================


class Versionable( metaclass=abc.ABCMeta ):

    def __getstate__(self):
        if not hasattr(self, "_class_version"):
            raise Exception("Your class must define _class_version class variable")
        # pylint: disable=E1101
        return dict(_class_version=self._class_version, **self.__dict__)

    def __setstate__(self, dict_):
        version_present_in_pickle = dict_.pop("_class_version", None)
        # pylint: disable=E1101
        if version_present_in_pickle == self._class_version:
            # pylint: disable=W0201
            self.__dict__ = dict_
        else:
            self._convertstate_( dict_, version_present_in_pickle )

    def _convertstate_(self, dict_, dictVersion_ ):
        # pylint: disable=E1101
        _LOGGER.info( "converting object from version %s to %s", dictVersion_, self._class_version )
        # pylint: disable=W0201
        self.__dict__ = dict_

#     @abc.abstractmethod
#     def _convertstate_(self, dict_, dictVersion_ ):
#         raise NotImplementedError('You need to define this method in derived class!')
