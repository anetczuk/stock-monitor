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

from stockmonitor.datatypes.datatypes import WalletData
from stockmonitor.datatypes.wallettypes import TransactionMatchMode


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

        dataobject.addTransactionData( "xxx", 2, 20.0, datetime.datetime(2, 2, 2), commission=0.4 )
        dataobject.addTransactionData( "xxx", 1, 20.0, datetime.datetime(1, 1, 1), commission=0.2 )
        dataobject.addTransactionData( "xxx", 3, 20.0, datetime.datetime(3, 3, 3), commission=0.6 )

        items = dataobject.transactions("xxx").items()
        self.assertEqual( len( items ), 3 )
        self.assertEqual( items[0].amount, 3 )
        self.assertEqual( items[1].amount, 2 )
        self.assertEqual( items[2].amount, 1 )

    def test_add_buy(self):
        dataobject = WalletData()
        matchMode = TransactionMatchMode.BEST

        self.assertEqual( dataobject.size(), 0 )

        dataobject.addTransactionData( "xxx", 1, 20.0, commission=1.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.addTransactionData( "xxx", 1, 10.0, commission=1.0 )
        self.assertEqual( dataobject.size(), 1 )

        self.assertEqual( dataobject.transactions("xxx").size(), 2 )

        items = dataobject.currentItems( matchMode )
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
        self.assertEqual( amount, 2 )
        self.assertEqual( unit_price, 16.0 )

    def test_add_buy_similar(self):
        dataobject = WalletData()
        matchMode = TransactionMatchMode.BEST

        self.assertEqual( dataobject.size(), 0 )

        dataobject.addTransactionData( "xxx", 1, 20.0, commission=1.0 )
        dataobject.addTransactionData( "xxx", 3, 20.0, commission=3.0 )

        self.assertEqual( dataobject.transactions("xxx").size(), 1 )

        items = dataobject.currentItems( matchMode )
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
        self.assertEqual( amount, 4 )
        self.assertEqual( unit_price, 21.0 )

    def test_add_sell_1(self):
        dataobject = WalletData()
        matchMode = TransactionMatchMode.BEST

        dataobject.addTransactionData( "xxx", 1, 20.0, commission=1.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.addTransactionData( "xxx", 1, 10.0, commission=1.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.addTransactionData( "xxx", -1, 10.0, commission=1.0 )
        self.assertEqual( dataobject.size(), 1 )

        items = dataobject.currentItems( matchMode )
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
        self.assertEqual( amount, 1 )
        self.assertEqual( unit_price, 21.0 )

    def test_add_sell_2(self):
        dataobject = WalletData()
        matchMode = TransactionMatchMode.BEST

        dataobject.addTransactionData( "xxx", 1, 10.0, commission=1.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.addTransactionData( "xxx", 1, 20.0, commission=1.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.addTransactionData( "xxx", -1, 20.0, commission=1.0 )
        self.assertEqual( dataobject.size(), 1 )

        items = dataobject.currentItems( matchMode )
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
        self.assertEqual( amount, 1 )
        self.assertEqual( unit_price, 11.0 )

    def test_add_sell_3(self):
        dataobject = WalletData()
        matchMode = TransactionMatchMode.BEST

        dataobject.addTransactionData( "xxx", 1, 20.0, commission=1.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.addTransactionData( "xxx", 1, 10.0, commission=1.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.addTransactionData( "xxx", -1, 15.0, commission=1.0 )
        self.assertEqual( dataobject.size(), 1 )

        items = dataobject.currentItems( matchMode )
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
        self.assertEqual( amount, 1 )
        self.assertEqual( unit_price, 21.0 )

    def test_add_sell_4(self):
        dataobject = WalletData()
        matchMode = TransactionMatchMode.BEST

        dataobject.addTransactionData( "xxx", 2, 10.0, commission=2.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.addTransactionData( "xxx", -1, 20.0, commission=2.0 )
        self.assertEqual( dataobject.size(), 1 )

        items = dataobject.currentItems( matchMode )
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
        self.assertEqual( amount, 1 )
        self.assertEqual( unit_price, 11.0 )
