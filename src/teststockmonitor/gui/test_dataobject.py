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

from stockmonitor.gui.dataobject import DataObject, WalletData


class WalletDataTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_add_buy(self):
        dataobject = WalletData()
        self.assertEqual( dataobject.size(), 0 )

        dataobject.add( "xxx", 1, 20.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", 1, 10.0 )
        self.assertEqual( dataobject.size(), 1 )

        self.assertEqual( dataobject.transactions("xxx").size(), 2 )

        items = dataobject.items()
        code, amount, unit_price = items[0]
        self.assertEqual( code, "xxx" )
        self.assertEqual( amount, 2 )
        self.assertEqual( unit_price, 15.0 )

    def test_add_buy_similar(self):
        dataobject = WalletData()
        self.assertEqual( dataobject.size(), 0 )

        dataobject.add( "xxx", 1, 20.0 )
        dataobject.add( "xxx", 3, 20.0 )

        self.assertEqual( dataobject.transactions("xxx").size(), 1 )

        items = dataobject.items()
        code, amount, unit_price = items[0]
        self.assertEqual( code, "xxx" )
        self.assertEqual( amount, 4 )
        self.assertEqual( unit_price, 20.0 )

    def test_add_sell_1(self):
        dataobject = WalletData()
        dataobject.add( "xxx", 1, 20.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", 1, 10.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", -1, 10.0 )
        self.assertEqual( dataobject.size(), 1 )

        items = dataobject.items()
        code, amount, unit_price = items[0]
        self.assertEqual( code, "xxx" )
        self.assertEqual( amount, 1 )
        self.assertEqual( unit_price, 20.0 )

    def test_add_sell_2(self):
        dataobject = WalletData()
        dataobject.add( "xxx", 1, 10.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", 1, 20.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", -1, 20.0 )
        self.assertEqual( dataobject.size(), 1 )

        items = dataobject.items()
        code, amount, unit_price = items[0]
        self.assertEqual( code, "xxx" )
        self.assertEqual( amount, 1 )
        self.assertEqual( unit_price, 10.0 )

    def test_add_sell_3(self):
        dataobject = WalletData()
        dataobject.add( "xxx", 1, 20.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", 1, 10.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", -1, 15.0 )
        self.assertEqual( dataobject.size(), 1 )

        items = dataobject.items()
        code, amount, unit_price = items[0]
        self.assertEqual( code, "xxx" )
        self.assertEqual( amount, 1 )
        self.assertEqual( unit_price, 20.0 )

    def test_add_sell_4(self):
        dataobject = WalletData()
        dataobject.add( "xxx", 2, 10.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", -1, 20.0 )
        self.assertEqual( dataobject.size(), 1 )

        items = dataobject.items()
        code, amount, unit_price = items[0]
        self.assertEqual( code, "xxx" )
        self.assertEqual( amount, 1 )
        self.assertEqual( unit_price, 10.0 )


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
