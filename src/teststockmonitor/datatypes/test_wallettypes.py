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
from stockmonitor.datatypes.wallettypes import TransHistory, Transaction,\
    TransactionMatchMode, TransactionsMatch, BuyTransactionsMatch, SellTransactionsMatch


class TransHistoryTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_amountBeforeDate(self):
        data = TransHistory()
        ## reverse order
        data.append( 10, 10.0, 0.1, datetime.datetime( year=2020, month=5, day=5 ) )
        data.append( -8, 20.0, 0.1, datetime.datetime( year=2020, month=5, day=3 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=1 ) )
        data.sort()

        amount = data.amountBeforeDate( datetime.date( year=2020, month=5, day=4 ) )
        self.assertEqual( amount, 1 )

        amount = data.amountBeforeDate( datetime.date( year=2020, month=5, day=3 ) )
        self.assertEqual( amount, 9 )

    def test_transactionsOverallProfit(self):
        data = TransHistory()
        ## reverse order
        data.append( 10, 10.0, 0.1, datetime.datetime( year=2020, month=5, day=5 ) )
        data.append( -8, 20.0, 0.1, datetime.datetime( year=2020, month=5, day=3 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=1 ) )
        data.sort()

        data.transactionsOverallProfit( False )

        amount = data.amountBeforeDate( datetime.date( year=2020, month=5, day=4 ) )
        self.assertEqual( amount, 1 )

        amount = data.amountBeforeDate( datetime.date( year=2020, month=5, day=3 ) )
        self.assertEqual( amount, 9 )

    def test_matchTransactionsRecent01(self):
        data = TransHistory()

        ## reverse order
        transList = \
            [ ( -200, 3.5, 0.1, datetime.datetime(2020, 10, 5, 15, 41, 33)),
              (  300, 2.0, 0.1, datetime.datetime(2020, 9, 25, 13, 11, 31)),
              (  200, 3.0, 0.1, datetime.datetime(2020, 8, 31,  9, 11, 26)),
              (  100, 4.0, 0.1, datetime.datetime(2020, 8, 25, 13, 11, 31)) ]

        data.appendList( transList )

        self.assertEqual( data.currentAmount(), 400 )

        transList: TransactionsMatch = data.matchTransactionsRecent()
        buyList: BuyTransactionsMatch = transList[0]
        self.assertEqual( len( buyList ), 2 )

        trans = buyList[0]
        self.assertEqual( trans.amount, 300 )
        self.assertEqual( trans.unitPrice, 2.0 )
        trans = buyList[1]
        self.assertEqual( trans.amount, 100 )
        self.assertEqual( trans.unitPrice, 3.0 )

    def test_matchTransactionsBestFit_sold(self):
        data = TransHistory()
        ## reverse order
        data.append(  5, 20.0, 1.0 )
        data.append( -5, 30.0, 1.5 )

        transList: TransactionsMatch = data.matchTransactionsBestFit()
        buyList = transList[0]
        self.assertEqual( len( buyList ), 0 )

    def test_matchTransactionsBestFit_01(self):
        data = TransHistory()
        ## reverse order
        data.append( 15, 10.0, 1.5 )
        data.append(  5, 20.0, 1.0 )
        data.append( -5, 30.0, 1.5 )

        transList: TransactionsMatch = data.matchTransactionsBestFit()
        buyList: BuyTransactionsMatch = transList[0]
        self.assertEqual( len( buyList ), 2 )

        trans: Transaction = buyList[0]
        self.assertEqual( trans.amount,  5 )
        self.assertEqual( trans.unitPrice, 20.0 )
        self.assertEqual( trans.commission, 1.0 )

        trans: Transaction = buyList[1]
        self.assertEqual( trans.amount, 10 )
        self.assertEqual( trans.unitPrice, 10.0 )
        self.assertEqual( trans.commission, 1.0 )

    def test_matchTransactionsBestFit_02(self):
        data = TransHistory()
        ## reverse order
        transList = \
            [ ( -9, 195.5, 0.0, datetime.datetime(2020, 9, 25, 11, 48, 52)),
              (  9, 168.0, 0.0, datetime.datetime(2020, 9, 23, 12, 14, 8)),
              (-12, 165.0, 0.0, datetime.datetime(2020, 7, 13, 10, 7, 12)),
              (  6, 148.0, 0.0, datetime.datetime(2020, 7, 8, 9, 48, 54)),
              (  6, 153.0, 0.0, datetime.datetime(2020, 7, 7, 15, 11, 23)),
              (-22,  99.0, 0.0, datetime.datetime(2020, 6, 12, 15, 36, 43)),
              ( 12,  88.0, 0.0, datetime.datetime(2020, 6, 9, 10, 27, 4)),
              ( 10,  90.2, 0.0, datetime.datetime(2020, 6, 8, 11, 28, 47)) ]
        data.appendList( transList )

        self.assertEqual( data.currentAmount(), 0 )

        transList: TransactionsMatch = data.matchTransactionsBestFit()
        buyList: BuyTransactionsMatch = transList[0]
        self.assertEqual( len( buyList ), 0 )

    def test_matchTransactionsBestFit_03(self):
        data = TransHistory()
        ## reverse order
        transList = \
            [ ( -400, 3.72, 0.1, datetime.datetime(2020, 10, 5, 15, 41, 33)),
              (  400, 3.17, 0.1, datetime.datetime(2020, 9, 25, 13, 11, 31)),
              (  200, 4.1,  0.1, datetime.datetime(2020, 8, 31, 9, 11, 26)) ]

        data.appendList( transList )

        self.assertEqual( data.currentAmount(), 200 )

        transList: TransactionsMatch = data.matchTransactionsBestFit()
        buyList = transList[0]
        self.assertEqual( len( buyList ), 1 )

        trans = buyList[0]
        self.assertEqual( trans.amount, 200 )
        self.assertEqual( trans.unitPrice, 4.1 )

    def test_matchTransactionsRecentProfit_01(self):
        data = TransHistory()

        ## reverse order
        transList = \
            [ ( -100, 3.5, 0.1, datetime.datetime(2020, 10, 5, 15, 41, 33)),
              (  300, 4.0, 0.1, datetime.datetime(2020, 9, 25, 13, 11, 31)),
              (  200, 3.0, 0.1, datetime.datetime(2020, 8, 31,  9, 11, 26)),
              (  100, 2.0, 0.1, datetime.datetime(2020, 8, 25, 13, 11, 31)) ]

        data.appendList( transList )

        self.assertEqual( data.currentAmount(), 500 )

        transList: TransactionsMatch = data.matchTransactionsRecentProfit()
        buyList = transList[0]
        self.assertEqual( len( buyList ), 3 )

        trans = buyList[1]
        self.assertEqual( trans.amount, 100 )
        self.assertEqual( trans.unitPrice, 3.0 )

    def test_sellTransactions_bestFit_01(self):
        data = TransHistory()
        matchMode = TransactionMatchMode.BEST

        ## reverse order
        transList = \
            [ ( -400, 3.72, 0.1, datetime.datetime(2020, 10, 5, 15, 41, 33)),
              (  400, 3.17, 0.1, datetime.datetime(2020, 9, 25, 13, 11, 31)),
              (  200, 4.1,  0.1, datetime.datetime(2020, 8, 31, 9, 11, 26)) ]

        data.appendList( transList )

        self.assertEqual( data.currentAmount(), 200 )

        transList: SellTransactionsMatch = data.sellTransactions( matchMode )

        self.assertEqual( len( transList ), 1 )

        sellTrans = transList[0][1]
        self.assertEqual( sellTrans.amount, -400 )
        self.assertEqual( sellTrans.unitPrice,  3.72 )

        buyTrans = transList[0][0]
        self.assertEqual( buyTrans.amount, 400 )
        self.assertEqual( buyTrans.unitPrice, 3.17 )

    def test_sellTransactions_bestFit_02(self):
        data = TransHistory()
        matchMode = TransactionMatchMode.BEST

        ## reverse order
        transList = \
            [ ( -400, 4.0, 0.1, datetime.datetime(2020, 10, 5, 15, 41, 33)),
              (  300, 3.0, 0.1, datetime.datetime(2020, 9, 25, 13, 11, 31)),
              (  200, 5.0, 0.1, datetime.datetime(2020, 8, 31,  9, 11, 26)),
              (  150, 2.0, 0.1, datetime.datetime(2020, 8, 25, 13, 11, 31)) ]

        data.appendList( transList )

        self.assertEqual( data.currentAmount(), 250 )

        transList: SellTransactionsMatch = data.sellTransactions( matchMode )

        self.assertEqual( len( transList ), 2 )

        sellTrans = transList[0][1]
        self.assertEqual( sellTrans.amount, -150 )
        self.assertEqual( sellTrans.unitPrice,  4.0 )

        buyTrans = transList[0][0]
        self.assertEqual( buyTrans.amount, 150 )
        self.assertEqual( buyTrans.unitPrice, 2.0 )

        sellTrans = transList[1][1]
        self.assertEqual( sellTrans.amount, -250 )
        self.assertEqual( sellTrans.unitPrice,  4.0 )

        buyTrans = transList[1][0]
        self.assertEqual( buyTrans.amount, 250 )
        self.assertEqual( buyTrans.unitPrice, 3.0 )

    def test_transactionsGain_best(self):
        data = TransHistory()
        matchMode = TransactionMatchMode.BEST

        ## reverse order
        transList = \
            [ ( -40, 5.0, 0.1, datetime.datetime(2020, 10, 5, 15, 41, 33)),
              (  30, 3.0, 0.1, datetime.datetime(2020, 9, 25, 13, 11, 31)),
              (  20, 4.0, 0.1, datetime.datetime(2020, 8, 31,  9, 11, 26)),
              (  20, 2.0, 0.1, datetime.datetime(2020, 8, 25, 13, 11, 31)) ]

        data.appendList( transList )

        self.assertEqual( data.currentAmount(), 30 )

        gainValue = data.transactionsGain( matchMode, False )
        self.assertEqual( gainValue, 100.0 )                     ## 20*3 + 20*2


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

        dataobject.add( "xxx", 2, 20.0, datetime.datetime(2, 2, 2), commission=0.4 )
        dataobject.add( "xxx", 1, 20.0, datetime.datetime(1, 1, 1), commission=0.2 )
        dataobject.add( "xxx", 3, 20.0, datetime.datetime(3, 3, 3), commission=0.6 )

        items = dataobject.transactions("xxx").items()
        self.assertEqual( len( items ), 3 )
        self.assertEqual( items[0].amount, 3 )
        self.assertEqual( items[1].amount, 2 )
        self.assertEqual( items[2].amount, 1 )

    def test_add_buy(self):
        dataobject = WalletData()
        matchMode = TransactionMatchMode.BEST

        self.assertEqual( dataobject.size(), 0 )

        dataobject.add( "xxx", 1, 20.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", 1, 10.0 )
        self.assertEqual( dataobject.size(), 1 )

        self.assertEqual( dataobject.transactions("xxx").size(), 2 )

        items = dataobject.currentItems( matchMode )
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
        self.assertEqual( amount, 2 )
        self.assertEqual( unit_price, 15.0 )

    def test_add_buy_similar(self):
        dataobject = WalletData()
        matchMode = TransactionMatchMode.BEST

        self.assertEqual( dataobject.size(), 0 )

        dataobject.add( "xxx", 1, 20.0 )
        dataobject.add( "xxx", 3, 20.0 )

        self.assertEqual( dataobject.transactions("xxx").size(), 1 )

        items = dataobject.currentItems( matchMode )
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
        self.assertEqual( amount, 4 )
        self.assertEqual( unit_price, 20.0 )

    def test_add_sell_1(self):
        dataobject = WalletData()
        matchMode = TransactionMatchMode.BEST

        dataobject.add( "xxx", 1, 20.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", 1, 10.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", -1, 10.0 )
        self.assertEqual( dataobject.size(), 1 )

        items = dataobject.currentItems( matchMode )
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
        self.assertEqual( amount, 1 )
        self.assertEqual( unit_price, 20.0 )

    def test_add_sell_2(self):
        dataobject = WalletData()
        matchMode = TransactionMatchMode.BEST

        dataobject.add( "xxx", 1, 10.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", 1, 20.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", -1, 20.0 )
        self.assertEqual( dataobject.size(), 1 )

        items = dataobject.currentItems( matchMode )
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
        self.assertEqual( amount, 1 )
        self.assertEqual( unit_price, 10.0 )

    def test_add_sell_3(self):
        dataobject = WalletData()
        matchMode = TransactionMatchMode.BEST

        dataobject.add( "xxx", 1, 20.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", 1, 10.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", -1, 15.0 )
        self.assertEqual( dataobject.size(), 1 )

        items = dataobject.currentItems( matchMode )
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
        self.assertEqual( amount, 1 )
        self.assertEqual( unit_price, 20.0 )

    def test_add_sell_4(self):
        dataobject = WalletData()
        matchMode = TransactionMatchMode.BEST

        dataobject.add( "xxx", 2, 10.0 )
        self.assertEqual( dataobject.size(), 1 )

        dataobject.add( "xxx", -1, 20.0 )
        self.assertEqual( dataobject.size(), 1 )

        items = dataobject.currentItems( matchMode )
        ticker, amount, unit_price = items[0]
        self.assertEqual( ticker, "xxx" )
        self.assertEqual( amount, 1 )
        self.assertEqual( unit_price, 10.0 )
