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
import copy

from PyQt5.QtWidgets import QUndoCommand


_LOGGER = logging.getLogger(__name__)


class DeleteFavGroupCommand( QUndoCommand ):

    def __init__(self, dataObject, favName, parentCommand=None):
        super().__init__(parentCommand)

        self.dataObject = dataObject
        self.favName = favName
        self.prevFavs = None

        self.setText( "Delete Fav Group: " + self.favName )

    def redo(self):
        favsObj = self.dataObject.favs
        self.prevFavs = copy.deepcopy( favsObj )
        favsObj.deleteFavGroup( self.favName )
        self.dataObject.favsChanged.emit()

    def undo(self):
        self.dataObject.favs = self.prevFavs
        self.dataObject.favsChanged.emit()
