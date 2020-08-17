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

from stockmonitor.gui.dataobject import DataObject


class DataObjectTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_addFavGroup(self):
        dataobject = DataObject()
        self.assertEqual( dataobject.undoStack.count(), 0 )
        dataobject.addFavGroup("xxx")
        self.assertEqual( dataobject.undoStack.count(), 1 )
        dataobject.addFavGroup("xxx")
        self.assertEqual( dataobject.undoStack.count(), 1 )

    def test_renameFavGrp(self):
        dataobject = DataObject()
        dataobject.addFavGroup("xxx")
        self.assertEqual( len(dataobject.favs.favs), 1 )

        dataobject.renameFavGroup("xxx", "yyy")
        self.assertEqual( len(dataobject.favs.favs), 1 )

        xxxFavs = dataobject.favs.getFavs( "xxx" )
        self.assertEqual( xxxFavs, None )

        yyyFavs = dataobject.favs.getFavs( "yyy" )
        self.assertNotEqual( yyyFavs, None )

    def test_deleteFavGrp(self):
        dataobject = DataObject()
        dataobject.addFavGroup("xxx")
        self.assertEqual( len(dataobject.favs.favs), 1 )

        dataobject.deleteFavGroup("xxx")
        self.assertEqual( len(dataobject.favs.favs), 0 )

    def test_deleteFavGrp_duplicates(self):
        dataobject = DataObject()
        dataobject.addFavGroup("xxx")
        dataobject.addFavGroup("xxx")
        self.assertEqual( len(dataobject.favs.favs), 1 )

        dataobject.deleteFavGroup("xxx")
        self.assertEqual( len(dataobject.favs.favs), 0 )

    def test_addFav_duplicates(self):
        dataobject = DataObject()
        dataobject.addFavGroup("xxx")
        self.assertEqual( len(dataobject.favs.favs), 1 )

        dataobject.addFav("xxx", "aaa")
        self.assertEqual( dataobject.undoStack.count(), 2 )

        dataobject.addFav("xxx", "aaa")
        self.assertEqual( dataobject.undoStack.count(), 2 )

    def test_addFav_duplicates_list(self):
        dataobject = DataObject()
        dataobject.addFav( "xxx", "aaa" )
        self.assertEqual( dataobject.undoStack.count(), 1 )

        dataobject.addFav( "xxx", ["aaa", "bbb"] )
        self.assertEqual( dataobject.undoStack.count(), 2 )
