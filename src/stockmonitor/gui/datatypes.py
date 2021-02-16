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

from enum import Enum, unique
import logging
import collections
import glob

from typing import Dict, List

from stockmonitor import persist
from stockmonitor.gui.wallettypes import WalletData, TransactionMatchMode


_LOGGER = logging.getLogger(__name__)


class FavData( persist.Versionable ):

    ## 0 - first version
    ## 1 - use ordererd dict
    ## 2 - use favs set
    ## 3 - use favs group list
    ## 4 - remove redundant field
    ## 5 - restore favs group as ordered dict
    ## 6 - use favs list
    _class_version = 6

    def __init__(self):
        ## Use list internally. For unknown reason Set causes persist to
        ## detect changes (difference in file content) even if elements does not change.
        self.favsList: Dict[ str, List[str] ] = collections.OrderedDict()

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

        if dictVersion_ == 2:
            ## convert ordererd dict to list
            favsDict = dict_["favs"]
            favsList = list()
            for key in favsDict.keys():
                pair = ( key, favsDict[key] )
                favsList.append( pair )
            del dict_["favs"]
            dict_["favsList"] = favsList
            dictVersion_ = 3

        if dictVersion_ == 3:
            ## remove redundant field
            if "favs" in dict_.keys():
                del dict_["favs"]
            dictVersion_ = 4

        if dictVersion_ == 4:
            favsList = dict_["favsList"]
            favsDict = collections.OrderedDict()
            for item in favsList:
                grp = item[0]
                favsDict[ grp ] = item[1]
            dict_["favsList"] = favsDict
            dictVersion_ = 5

        if dictVersion_ == 5:
            favsDict = dict_["favsList"]
            for key in favsDict.keys():
                favsDict[ key ] = list( favsDict[ key ] )
            dict_["favsList"] = favsDict
            dictVersion_ = 6

        # pylint: disable=W0201
        self.__dict__ = dict_

    def containsGroup(self, group):
        found = self.getFavs( group )
        return found is not None

    def getFavGroups(self):
        return self.favsList.keys()

    def getFavs(self, group) -> List[str]:
        return self.favsList.get( group, None )

    def getFavsAll(self):
        ret = set()
        for val in self.favsList.values():
            ret = ret | set( val )
        return ret

    def addFavGroup(self, name):
        if name not in self.favsList:
            self.favsList[name] = list()

    def renameFavGroup(self, fromName, toName):
#         self.favsList[toName] = self.favsList.pop(fromName)
        dLen = len(self.favsList)
        for _ in range(dLen):
            k, v = self.favsList.popitem(False)
            newKey = toName if fromName == k else k
            self.favsList[ newKey ] = v

    def deleteFavGroup(self, name):
        del self.favsList[name]

    def reorderFavGroups(self, newOrder):
        for item in reversed(newOrder):
            # pylint: disable=E1101
            self.favsList.move_to_end( item, False )

    def setFavs(self, group, items):
        itemsList = list( items )
        self.addFavGroup( group )
        newSet = set( itemsList )
        self.favsList[group] = list( newSet )

    def addFav(self, group, items):
        itemsList = list( items )
        self.addFavGroup( group )
        newSet = set( self.favsList[group] + itemsList )          ## sum of sets
        self.favsList[group] = list( newSet )

    def deleteFav(self, group, items):
        _LOGGER.info( "Removing favs: %s from group %s", items, group )
        itemsList = set( items )
        if group not in self.favsList:
            _LOGGER.warning("Unable to find group")
            return
        groupList = self.favsList[group]
        for item in itemsList:
            groupList.remove( item )
        self.favsList[group] = groupList


## ================================================================


class MarkerEntry( persist.Versionable ):

    @unique
    class OperationType(Enum):
        BUY  = ()
        SELL = ()

        def __new__(cls):
            value = len(cls.__members__)  # note no + 1
            obj = object.__new__(cls)
            # pylint: disable=W0212
            obj._value_ = value
            return obj

    ## ================================================

    ## 0 - first version
    ## 1 - renamed field 'color' to '_color'
    _class_version = 1

    def __init__(self):
        self.ticker = None
        self.value = None
        self.amount = None
        self.operation = None
        self._color = None

    def _convertstate_(self, dict_, dictVersion_ ):
        _LOGGER.info( "converting object from version %s to %s", dictVersion_, self._class_version )

        if dictVersion_ is None:
            dictVersion_ = 0

        if dictVersion_ < 1:
            colorField = dict_.pop( "color" )
            if colorField is not None:
                colorField = colorField.upper()
            dict_[ "_color" ] = colorField

        # pylint: disable=W0201
        self.__dict__ = dict_

    @property
    def color(self) -> str:
        return self._color

    @color.setter
    def color(self, value: str):
        if value is None:
            self._color = None
            return
        self._color = value.upper()

    def operationName(self) -> str:
        if self.operation is None:
            return None
        return self.operation.name

    def setOperation(self, operation ):
        self.operation = operation
        if self.color is not None:
            return
        ## set default color
        if operation is MarkerEntry.OperationType.BUY:
            self.color = "orange"
#             self.color = "#6FD7FF"
#             self.color = "#FF9191"
        elif operation is MarkerEntry.OperationType.SELL:
            self.color = "orange"
#             self.color = "#6FD7FF"

    def printData(self) -> str:
        return str( self.ticker ) + " " + str( self.value ) + " " + str( self.amount ) + " " + str( self.operation )


class MarkersContainer( persist.Versionable ):

    ## 0 - first version
    _class_version = 0

    def __init__(self):
        self.markers: List[MarkerEntry] = list()

    def _convertstate_(self, dict_, dictVersion_ ):
        _LOGGER.info( "converting object from version %s to %s", dictVersion_, self._class_version )

        if dictVersion_ is None:
            dictVersion_ = 0

        # pylint: disable=W0201
        self.__dict__ = dict_

    def size(self):
        return len( self.markers )

    def get(self, index ):
        return self.markers[ index ]

    def getBestMatchingColor(self, ticker, stockPrice):
        ## return best color
        if ticker is None:
            return None
        bestBuy  = None
        bestSell = None
        for item in self.markers:
            if item.ticker != ticker:
                continue
            if item.value is None:
                ## invalid value
                continue
            if item.operation is MarkerEntry.OperationType.BUY:
                ## check for cheap stock
                if item.value < stockPrice:
                    ## marker value is cheaper than stock value -- skip
                    continue
                if bestBuy is None or item.value < bestBuy.value:
                    bestBuy = item
            elif item.operation is MarkerEntry.OperationType.SELL:
                ## check of expensive stock
                if item.value > stockPrice:
                    ## marker value is more expensive than stock value -- skip
                    continue
                if bestSell is None or item.value > bestSell.value:
                    bestSell = item
        if bestSell is not None:
            return bestSell.color.lower()       ## lower for tests compatibility
        if bestBuy is not None:
            return bestBuy.color.lower()        ## lower for tests compatibility
        return None

    def add( self, ticker, value, amount, operation: MarkerEntry.OperationType, colorName: str = None ):
        entry = MarkerEntry()
        entry.ticker = ticker
        entry.value = value
        entry.amount = amount
        entry.operation = operation
        entry.color = colorName
        self.addItem( entry )

    def addItem(self, entry):
        self.markers.append( entry )

    def addItemList(self, entries):
        self.markers += entries

    def replaceItem(self, oldEntry, newEntry):
        _LOGGER.debug( "replacing marker %s with %s", oldEntry, newEntry )
        for i, _ in enumerate( self.markers ):
            currItem = self.markers[i]
            if currItem == oldEntry:
                self.markers[i] = newEntry
#                 self.sort()
                return True
        _LOGGER.debug( "replacing failed" )
        return False

    def deleteItem(self, entry):
        self.markers.remove( entry )

    def deleteItemsList(self, entries):
        self.markers = [x for x in self.markers if x not in entries]


## ================================================================


class UserContainer():

    ## 0 - first version
    ## 1 - wallet added
    ## 2 - extract History class from WalletData
    ## 3 - transactions match mode
    ## 4 - markers
    _class_version = 4

    def __init__(self):
        self.favs   = FavData()
        self.notes  = { "notes": "" }        ## default notes
        self.wallet = WalletData()
        self.transactionsMatchMode = TransactionMatchMode.BEST
        self.markers = MarkersContainer()

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

        outputFile = outputDir + "/wallet.obj"
        if persist.store_object( self.wallet, outputFile ) is True:
            changed = True

        outputFile = outputDir + "/transactions_match.obj"
        if persist.store_object( self.transactionsMatchMode, outputFile ) is True:
            changed = True

        outputFile = outputDir + "/markers.obj"
        if persist.store_object( self.markers, outputFile ) is True:
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

        inputFile = inputDir + "/wallet.obj"
        self.wallet = persist.load_object( inputFile, self._class_version )
        if self.wallet is None:
            self.wallet = WalletData()

        inputFile = inputDir + "/transactions_match.obj"
        self.transactionsMatchMode = persist.load_object( inputFile, self._class_version )
        if self.transactionsMatchMode is None:
            self.transactionsMatchMode = TransactionMatchMode.BEST

        inputFile = inputDir + "/markers.obj"
        self.markers = persist.load_object( inputFile, self._class_version )
        if self.markers is None:
            self.markers = MarkersContainer()
