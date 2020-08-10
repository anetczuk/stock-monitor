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
from typing import Dict, List
import glob

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QUndoStack

from stockmonitor import persist
from stockmonitor.gui.command.addfavgroupcommand import AddFavGroupCommand
from stockmonitor.gui.command.deletefavgroupcommand import DeleteFavGroupCommand
from stockmonitor.gui.command.renamefavgroupcommand import RenameFavGroupCommand
from stockmonitor.dataaccess.gpwdata import GpwCurrentData
from stockmonitor.gui.command.addfavcommand import AddFavCommand
from stockmonitor.gui.command.deletefavcommand import DeleteFavCommand


_LOGGER = logging.getLogger(__name__)


class FavData():
    
    def __init__(self):
        self.favs: Dict[ str, List[str] ] = dict()

    def favGroupsList(self):
        return self.favs.keys()

    def getFavs(self, group):
        return self.favs.get( group, None )

    def addFavGroup(self, name):
        if not name in self.favs:
            self.favs[name] = list()

    def renameFavGroup(self, fromName, toName):
        self.favs[toName] = self.favs.pop(fromName)

    def deleteFavGroup(self, name):
        del self.favs[name]
    
    def addFav(self, group, item):
        self.addFavGroup( group )
        self.favs[group].append( item )
    
    def deleteFav(self, group, item):
        if group in self.favs:
            self.favs[group].remove( item )


class DataObject( QObject ):

    ## 0 - first version
    _class_version = 0

    ## added, modified or removed
    favsChanged      = pyqtSignal()
    stockDataChanged = pyqtSignal()

    def __init__(self, parent: QWidget=None):
        super().__init__( parent )
        self.parentWidget = parent

        self.favs = FavData()
        self.currentStockData = GpwCurrentData()
        
        self.undoStack = QUndoStack(self)

    def store( self, outputDir ):
        changed = False

        outputFile = outputDir + "/version.obj"
        if persist.store_object( self._class_version, outputFile ) is True:
            changed = True

        outputFile = outputDir + "/favs.obj"
        if persist.store_object( self.favs, outputFile ) is True:
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

    ## ======================================================================

    def addFavGroup(self, name):
        self.undoStack.push( AddFavGroupCommand( self, name ) )

    def renameFavGroup(self, fromName, toName):
        self.undoStack.push( RenameFavGroupCommand( self, fromName, toName ) )

    def deleteFavGroup(self, name):
        self.undoStack.push( DeleteFavGroupCommand( self, name ) )

    def addFav(self, group, favItem):
        self.undoStack.push( AddFavCommand( self, group, favItem ) )

    def deleteFav(self, group, favItem):
        self.undoStack.push( DeleteFavCommand( self, group, favItem ) )

    def getFavStock(self, favGroup):
        stockList = self.favs.getFavs( favGroup )
        return self.currentStockData.getStockData( stockList )

    def refreshStockData(self):
        self.currentStockData.refreshData()
