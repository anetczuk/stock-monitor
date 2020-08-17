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
import collections
import glob
from typing import Dict, Set

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QUndoStack

from stockmonitor import persist
from stockmonitor.gui.command.addfavgroupcommand import AddFavGroupCommand
from stockmonitor.gui.command.deletefavgroupcommand import DeleteFavGroupCommand
from stockmonitor.gui.command.renamefavgroupcommand import RenameFavGroupCommand
from stockmonitor.dataaccess.gpwdata import GpwCurrentData
from stockmonitor.gui.command.addfavcommand import AddFavCommand
from stockmonitor.gui.command.deletefavcommand import DeleteFavCommand
from stockmonitor.gui.command.reorderfavgroupscommand import ReorderFavGroupsCommand


_LOGGER = logging.getLogger(__name__)


class FavData( persist.Versionable ):

    ## 0 - first version
    ## 1 - use ordererd dict
    ## 2 - use favs set
    _class_version = 2

    def __init__(self):
        self.favs: Dict[ str, Set[str] ] = collections.OrderedDict()

    def _convertstate_(self, dict_, dictVersion_ ):
        _LOGGER.info( "converting object from version %s to %s", dictVersion_, self._class_version )

        if dictVersion_ is None:
            dictVersion_ = -1

        if dictVersion_ < 0:
            ## nothing to do
            dictVersion_ = 0

        if dictVersion_ == 0:
            ## use ordererd dict
            oldDict = dict_["favs"]
            newDict = collections.OrderedDict( oldDict )
            dict_["favs"] = newDict
            dictVersion_ = 1

        if dictVersion_ == 1:
            ## use ordererd dict
            favsDict = dict_["favs"]
            for key in favsDict.keys():
                favsDict[key] = set( favsDict[key] )
            dict_["favs"] = favsDict
            dictVersion_ = 2

        # pylint: disable=W0201
        self.__dict__ = dict_

    def containsGroup(self, group):
        found = self.getFavs( group )
        return found is not None

    def favGroupsList(self):
        return self.favs.keys()

    def getFavs(self, group) -> Set[str]:
        return self.favs.get( group, None )

    def addFavGroup(self, name):
        if name not in self.favs:
            self.favs[name] = set()

    def renameFavGroup(self, fromName, toName):
        self.favs[toName] = self.favs.pop(fromName)

    def deleteFavGroup(self, name):
        del self.favs[name]

    def reorderFavGroups(self, newOrder):
        for item in reversed(newOrder):
            # pylint: disable=E1101
            self.favs.move_to_end( item, False )

    def addFav(self, group, items):
        itemsSet = set( items )
        self.addFavGroup( group )
        self.favs[group] = self.favs[group] | itemsSet          ## sum of sets

    def deleteFav(self, group, items):
        _LOGGER.info( "Removing favs: %s from group %s", items, group )
        itemsList = set( items )
        if group not in self.favs:
            _LOGGER.warning("Unable to find group")
            return
        groupList = self.favs[group]
        for item in itemsList:
            groupList.remove( item )
        self.favs[group] = groupList


class DataContainer():
    ## 0 - first version
    _class_version = 0

    def __init__(self):
        self.favs  = FavData()
        self.notes = { "notes": "" }        ## default notes

    def store( self, outputDir ):
        changed = False

        outputFile = outputDir + "/version.obj"
        if persist.store_object( self._class_version, outputFile ) is True:
            changed = True

        outputFile = outputDir + "/favs.obj"
        if persist.store_object( self.favs, outputFile ) is True:
            changed = True

        outputFile = outputDir + "/notes.obj"
        if persist.store_object( self.notes, outputFile ) is True:
            changed = True

        ## backup data
        objFiles = glob.glob( outputDir + "/*.obj" )
        storedZipFile = outputDir + "/data.zip"
        persist.backup_files( objFiles, storedZipFile )

        return changed

    def load( self, inputDir ):
        inputFile = inputDir + "/version.obj"
        mngrVersion = persist.load_object( inputFile, self._class_version )
        if mngrVersion != self. _class_version:
            _LOGGER.info( "converting object from version %s to %s", mngrVersion, self._class_version )
            ## do nothing for now

        inputFile = inputDir + "/favs.obj"
        self.favs = persist.load_object( inputFile, self._class_version )
        if self.favs is None:
            self.favs = FavData()

        inputFile = inputDir + "/notes.obj"
        self.notes = persist.load_object( inputFile, self._class_version )
        if self.notes is None:
            self.notes = { "notes": "" }


class DataObject( QObject ):

    favsAdded           = pyqtSignal( str )     ## emit group
    favsRemoved         = pyqtSignal( str )     ## emit group
    favsReordered       = pyqtSignal()
    favsChanged         = pyqtSignal()

    stockDataChanged    = pyqtSignal()
    stockHeadersChanged = pyqtSignal()

    def __init__(self, parent: QWidget=None):
        super().__init__( parent )
        self.parentWidget = parent

        self.dataContainer                          = DataContainer()
        self.currentStockData                       = GpwCurrentData()
        self.currentStockHeaders: Dict[ int, str ]  = dict()

        self.undoStack = QUndoStack(self)

    def store( self, outputDir ):
        outputFile = outputDir + "/gpwcurrentheaders.obj"
        persist.store_object( self.currentStockHeaders, outputFile )
        return self.dataContainer.store( outputDir )

    def load( self, inputDir ):
        self.dataContainer.load( inputDir )
        inputFile = inputDir + "/gpwcurrentheaders.obj"
        headers = persist.load_object_simple( inputFile, dict() )
        self.setCurrentStockHeaders( headers )

    @property
    def favs(self) -> FavData:
        return self.dataContainer.favs

    @favs.setter
    def favs(self, newData: FavData):
        self.dataContainer.favs = newData

    @property
    def notes(self) -> Dict[str, str]:
        return self.dataContainer.notes

    @notes.setter
    def notes(self, newData: Dict[str, str]):
        self.dataContainer.notes = newData

    ## ======================================================================

    def addFavGroup(self, name):
        if self.favs.containsGroup( name ):
            return
        self.undoStack.push( AddFavGroupCommand( self, name ) )

    def renameFavGroup(self, fromName, toName):
        self.undoStack.push( RenameFavGroupCommand( self, fromName, toName ) )

    def deleteFavGroup(self, name):
        self.undoStack.push( DeleteFavGroupCommand( self, name ) )

    def addFav(self, group, favItem):
        favsSet = self.favs.getFavs( group )
        if favsSet is None:
            favsSet = set()
        itemsSet = set( favItem )
        diffSet = itemsSet - favsSet
        if len(diffSet) < 1:
            return
        self.undoStack.push( AddFavCommand( self, group, diffSet ) )

    def deleteFav(self, group, favItem):
        itemsSet = set( favItem )
        self.undoStack.push( DeleteFavCommand( self, group, itemsSet ) )

    def reorderFavGroups(self, newOrder):
        self.undoStack.push( ReorderFavGroupsCommand( self, newOrder ) )

    def getFavStock(self, favGroup):
        stockList = self.favs.getFavs( favGroup )
        return self.currentStockData.getStockData( stockList )

    ## ======================================================================

    def refreshStockData(self):
        self.currentStockData.refreshData()
        self.stockDataChanged.emit()

    def setCurrentStockHeaders(self, headersDict):
        self.currentStockHeaders = headersDict
        self.stockHeadersChanged.emit()
