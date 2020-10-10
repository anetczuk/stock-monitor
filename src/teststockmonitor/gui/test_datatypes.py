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

import datetime
import pickle
from typing import List, Tuple

from stockmonitor.gui.dataobject import WalletData, FavData
from stockmonitor.gui.datatypes import TransHistory


class FavDataTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_pickle(self):
        dataMem1 = pickle.dumps( FavData() )
        dataMem2 = pickle.dumps( FavData() )
        self.assertEqual( dataMem1, dataMem2 )


class WalletDataTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_add_sort(self):
        dataobject = WalletData()
        self.assertEqual( dataobject.size(), 0 )

        dataobject.add( "xxx", 2, 20.0, datetime.datetime(2, 2, 2) )
        dataobject.add( "xxx", 1, 20.0, datetime.datetime(1, 1, 1) )
        dataobject.add( "xxx", 3, 20.0, datetime.datetime(3, 3, 3) )

        items = dataobject.transactions("xxx").items()
        self.assertEqual( len( items ), 3 )
        self.assertEqual( items[0][0], 3 )
        self.assertEqual( items[1][0], 2 )
        self.assertEqual( items[2][0], 1 )

    def test_add_buy(self):
        dataobject = WalletData()
        self.assertEqual( dataobject.size(), 0 )

        dataobject.add( "xxx", 1, 20.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", 1, 10.0 )
        self.assertEqual( dataobject.size(), 1 )

        self.assertEqual( dataobject.transactions("xxx").size(), 2 )

        items = dataobject.items()
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
        self.assertEqual( amount, 2 )
        self.assertEqual( unit_price, 15.0 )

    def test_add_buy_similar(self):
        dataobject = WalletData()
        self.assertEqual( dataobject.size(), 0 )

        dataobject.add( "xxx", 1, 20.0 )
        dataobject.add( "xxx", 3, 20.0 )

        self.assertEqual( dataobject.transactions("xxx").size(), 1 )

        items = dataobject.items()
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
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
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
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
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
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
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
        self.assertEqual( amount, 1 )
        self.assertEqual( unit_price, 20.0 )

    def test_add_sell_4(self):
        dataobject = WalletData()
        dataobject.add( "xxx", 2, 10.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", -1, 20.0 )
        self.assertEqual( dataobject.size(), 1 )

        items = dataobject.items()
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
        self.assertEqual( amount, 1 )
        self.assertEqual( unit_price, 10.0 )

    def test_currentTransactionsBestFit_sold(self):
        data = TransHistory()
        ## reverse order
        data.append(  5, 20.0 )
        data.append( -5, 30.0 )

        transList: List[ Tuple[int, float, datetime] ] = data.currentTransactionsBestFit()
        self.assertEqual( len( transList ), 0 )

    def test_currentTransactionsBestFit_01(self):
        data = TransHistory()
        ## reverse order
        data.append( 10, 10.0 )
        data.append(  5, 20.0 )
        data.append( -5, 30.0 )

        transList: List[ Tuple[int, float, datetime] ] = data.currentTransactionsBestFit()
        self.assertEqual( len( transList ), 2 )

        trans = transList[0]
        self.assertEqual( trans[0],  5 )
        self.assertEqual( trans[1], 20.0 )
        trans = transList[1]
        self.assertEqual( trans[0],  5 )
        self.assertEqual( trans[1], 10.0 )

    def test_currentTransactionsBestFit_02(self):
        data = TransHistory()
        ## reverse order
        transList = \
            [ ( -9, 195.5, datetime.datetime(2020, 9, 25, 11, 48, 52)),
              (  9, 168.0, datetime.datetime(2020, 9, 23, 12, 14, 8)),
              (-12, 165.0, datetime.datetime(2020, 7, 13, 10, 7, 12)),
              (  6, 148.0, datetime.datetime(2020, 7, 8, 9, 48, 54)),
              (  6, 153.0, datetime.datetime(2020, 7, 7, 15, 11, 23)),
              (-22, 99.0, datetime.datetime(2020, 6, 12, 15, 36, 43)),
              ( 12, 88.0, datetime.datetime(2020, 6, 9, 10, 27, 4)),
              ( 10, 90.2, datetime.datetime(2020, 6, 8, 11, 28, 47)) ]
        data.appendList( transList )

        self.assertEqual( data.currentAmount(), 0 )

        transList: List[ Tuple[int, float, datetime] ] = data.currentTransactionsBestFit()
        self.assertEqual( len( transList ), 0 )

    def test_currentTransactionsBestFit_03(self):
        data = TransHistory()
        ## reverse order
        transList = \
            [ ( -400, 3.72, datetime.datetime(2020, 10, 5, 15, 41, 33)),
              (  400, 3.17, datetime.datetime(2020, 9, 25, 13, 11, 31)),
              (  200, 4.1, datetime.datetime(2020, 8, 31, 9, 11, 26)) ]

        data.appendList( transList )

        self.assertEqual( data.currentAmount(), 200 )

        transList: List[ Tuple[int, float, datetime] ] = data.currentTransactionsBestFit()
        self.assertEqual( len( transList ), 1 )

        trans = transList[0]
        self.assertEqual( trans[0], 200 )
        self.assertEqual( trans[1], 4.1 )
