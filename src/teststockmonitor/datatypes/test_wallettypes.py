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
import pandas

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

    def test_findIndex(self):
        data = TransHistory()
        data.append( -8, 20.0, 0.1, datetime.datetime( year=2020, month=5, day=5, hour=16 ) )
        data.append( -8, 20.0, 0.1, datetime.datetime( year=2020, month=5, day=4, hour=16 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=4, hour=12 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=4, hour=8 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=3, hour=8 ) )
        data.sort()                 ## reverse order

        indexTime = datetime.datetime( year=2020, month=5, day=4, hour=10 )
        foundIndex = data.findIndex( indexTime )
        self.assertEqual( foundIndex, 3 )

    def test_findIndexBefore_before(self):
        data = TransHistory()
        data.append( -8, 20.0, 0.1, datetime.datetime( year=2020, month=5, day=4 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=2 ) )
        data.sort()                 ## reverse order

        indexDate = datetime.date( 2020, 5, 1 )
        foundIndex = data.findIndexBefore( indexDate )
        self.assertEqual( foundIndex, 2 )

    def test_findIndexBefore_start(self):
        data = TransHistory()
        data.append( -8, 20.0, 0.1, datetime.datetime( year=2020, month=5, day=4 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=2 ) )
        data.sort()                 ## reverse order

        indexDate = datetime.date( 2020, 5, 2 )
        foundIndex = data.findIndexBefore( indexDate )
        self.assertEqual( foundIndex, 2 )

    def test_findIndexBefore_middle(self):
        data = TransHistory()
        data.append( -8, 20.0, 0.1, datetime.datetime( year=2020, month=5, day=4 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=2 ) )
        data.sort()                 ## reverse order

        indexDate = datetime.date( 2020, 5, 3 )
        foundIndex = data.findIndexBefore( indexDate )
        self.assertEqual( foundIndex, 1 )

    def test_findIndexBefore_end(self):
        data = TransHistory()
        data.append( -8, 20.0, 0.1, datetime.datetime( year=2020, month=5, day=4 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=2 ) )
        data.sort()                 ## reverse order

        indexDate = datetime.date( 2020, 5, 4 )
        foundIndex = data.findIndexBefore( indexDate )
        self.assertEqual( foundIndex, 1 )

    def test_findIndexBefore_after(self):
        data = TransHistory()
        data.append( -8, 20.0, 0.1, datetime.datetime( year=2020, month=5, day=4 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=2 ) )
        data.sort()                 ## reverse order

        indexDate = datetime.date( 2020, 5, 5 )
        foundIndex = data.findIndexBefore( indexDate )
        self.assertEqual( foundIndex, 0 )

    def test_splitTransactions01(self):
        data = TransHistory()
        data.append( -8, 20.0, 0.1, datetime.datetime( year=2020, month=5, day=6 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=4 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=2 ) )
        data.sort()                 ## reverse order

        transBefore, transAfter = data.splitTransactions( 1, False )
        self.assertEqual( transBefore.size(), 2 )
        self.assertEqual( transAfter.size(), 1 )

    def test_splitTransactions02(self):
        data = TransHistory()
        data.append( -8, 20.0, 0.1, datetime.datetime( year=2020, month=5, day=6 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=4 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=2 ) )
        data.sort()                 ## reverse order

        transBefore, transAfter = data.splitTransactions( 1, True )
        self.assertEqual( transBefore.size(), 1 )
        self.assertEqual( transAfter.size(), 2 )

    def test_transactionsBefore(self):
        data = TransHistory()
        data.append( -8, 20.0, 0.1, datetime.datetime( year=2020, month=5, day=4 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=2 ) )
        data.sort()                 ## reverse order

        indexDate = datetime.date( 2020, 5, 4 )
        retList: TransHistory = data.transactionsBefore( indexDate )
        self.assertEqual( retList.size(), 1 )
        self.assertEqual( retList[0].transTime, data[1].transTime )

    def test_transactionsAfter(self):
        data = TransHistory()
        data.append( -8, 20.0, 0.1, datetime.datetime( year=2020, month=5, day=4 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=2 ) )
        data.sort()                 ## reverse order

        indexDate = datetime.date( 2020, 5, 4 )
        retList: TransHistory = data.transactionsAfter( indexDate )
        self.assertEqual( retList.size(), 1 )
        self.assertEqual( retList[0].transTime, data[0].transTime )

    def test_transactionsOverallProfit(self):
        data = TransHistory()
        ## reverse order
        data.append( 10, 10.0, 0.1, datetime.datetime( year=2020, month=5, day=5 ) )
        data.append( -8, 20.0, 0.1, datetime.datetime( year=2020, month=5, day=3 ) )
        data.append(  9, 30.0, 0.1, datetime.datetime( year=2020, month=5, day=1 ) )
        data.sort()

        data.transactionsOverallProfit()

        amount = data.amountBeforeDate( datetime.date( year=2020, month=5, day=4 ) )
        self.assertEqual( amount, 1 )

        amount = data.amountBeforeDate( datetime.date( year=2020, month=5, day=3 ) )
        self.assertEqual( amount, 9 )

    def test_matchStockBefore_empty(self):
        data = TransHistory()

        dataframe = pandas.DataFrame( {'t': [],
                                       'c': []} )

        indexList = data.matchStockBefore( dataframe )
        self.assertEqual( indexList, [] )

    def test_matchStockBefore_before(self):
        data = TransHistory()

        ## reverse order (amount, unit, commission, trans time)
        transList = \
            [ ( 100, 4.0, 0.0, datetime.datetime(2020, 10, 2, 12, 0, 0)) ]

        data.appendList( transList )

        dataframe = pandas.DataFrame( [ [ datetime.datetime(2020, 10,  5, 12, 0, 0), 10.0 ],
                                        [ datetime.datetime(2020, 10, 10, 12, 0, 0), 12.0 ]
                                        ], columns=[ 't', 'c' ] )

        indexList = data.matchStockBefore( dataframe )
        self.assertEqual( indexList, [0] )

    def test_matchStockBefore_middle(self):
        data = TransHistory()

        ## reverse order (amount, unit, commission, trans time)
        transList = \
            [ ( 100, 4.0, 0.0, datetime.datetime(2020, 10, 8, 12, 0, 0)) ]

        data.appendList( transList )

        dataframe = pandas.DataFrame( [ [ datetime.datetime(2020, 10,  5, 12, 0, 0), 10.0 ],
                                        [ datetime.datetime(2020, 10, 10, 12, 0, 0), 12.0 ]
                                        ], columns=[ 't', 'c' ] )

        indexList = data.matchStockBefore( dataframe )
        self.assertEqual( indexList, [1] )

    def test_matchStockBefore_after(self):
        data = TransHistory()

        ## reverse order (amount, unit, commission, trans time)
        transList = \
            [ ( 100, 4.0, 0.0, datetime.datetime(2020, 10, 11, 12, 0, 0)) ]

        data.appendList( transList )

        dataframe = pandas.DataFrame( [ [ datetime.datetime(2020, 10,  5, 12, 0, 0), 10.0 ],
                                        [ datetime.datetime(2020, 10, 10, 12, 0, 0), 12.0 ]
                                        ], columns=[ 't', 'c' ] )

        indexList = data.matchStockBefore( dataframe )
        self.assertEqual( indexList, [2] )

    def test_matchStockBefore03(self):
        data = TransHistory()

        ## reverse order (amount, unit, commission, trans time)
        transList = \
            [ ( 100, 5.0, 0.0, datetime.datetime(2020, 10, 8, 12, 0, 0)),
              ( 100, 4.0, 0.0, datetime.datetime(2020, 10, 4, 12, 0, 0)),
              ( 100, 4.0, 0.0, datetime.datetime(2020, 10, 3, 12, 0, 0)) ]

        data.appendList( transList )

        dataframe = pandas.DataFrame( [ [ datetime.datetime(2020, 10,  5, 12, 0, 0), 10.0 ],
                                        [ datetime.datetime(2020, 10, 10, 12, 0, 0), 12.0 ]
                                        ], columns=[ 't', 'c' ] )

        indexList = data.matchStockBefore( dataframe )
        self.assertEqual( indexList, [1, 0, 0] )

    def test_matchStockAfter_empty(self):
        data = TransHistory()

        dataframe = pandas.DataFrame( {'t': [],
                                       'c': []} )

        indexList = data.matchStockAfter( dataframe )
        self.assertEqual( indexList, [] )

    def test_matchStockAfter_before(self):
        data = TransHistory()

        ## reverse order (amount, unit, commission, trans time)
        transList = \
            [ ( 100, 4.0, 0.0, datetime.datetime(2020, 10, 2, 12, 0, 0)) ]

        data.appendList( transList )

        dataframe = pandas.DataFrame( [ [ datetime.datetime(2020, 10,  5, 12, 0, 0), 10.0 ],
                                        [ datetime.datetime(2020, 10, 10, 12, 0, 0), 12.0 ]
                                        ], columns=[ 't', 'c' ] )

        indexList = data.matchStockAfter( dataframe )
        self.assertEqual( indexList, [2] )

    def test_matchStockAfter_middle(self):
        data = TransHistory()

        ## reverse order (amount, unit, commission, trans time)
        transList = \
            [ ( 100, 4.0, 0.0, datetime.datetime(2020, 10, 8, 12, 0, 0)) ]

        data.appendList( transList )

        dataframe = pandas.DataFrame( [ [ datetime.datetime(2020, 10,  5, 12, 0, 0), 10.0 ],
                                        [ datetime.datetime(2020, 10, 10, 12, 0, 0), 12.0 ]
                                        ], columns=[ 't', 'c' ] )

        indexList = data.matchStockAfter( dataframe )
        self.assertEqual( indexList, [1] )

    def test_matchStockAfter_after(self):
        data = TransHistory()

        ## reverse order (amount, unit, commission, trans time)
        transList = \
            [ ( 100, 4.0, 0.0, datetime.datetime(2020, 10, 11, 12, 0, 0)) ]

        data.appendList( transList )

        dataframe = pandas.DataFrame( [ [ datetime.datetime(2020, 10,  5, 12, 0, 0), 10.0 ],
                                        [ datetime.datetime(2020, 10, 10, 12, 0, 0), 12.0 ]
                                        ], columns=[ 't', 'c' ] )

        indexList = data.matchStockAfter( dataframe )
        self.assertEqual( indexList, [0] )

    def test_matchStockAfter03(self):
        data = TransHistory()

        ## reverse order (amount, unit, commission, trans time)
        transList = \
            [ ( 100, 5.0, 0.0, datetime.datetime(2020, 10, 8, 12, 0, 0)),
              ( 100, 4.0, 0.0, datetime.datetime(2020, 10, 4, 12, 0, 0)),
              ( 100, 4.0, 0.0, datetime.datetime(2020, 10, 3, 12, 0, 0)) ]

        data.appendList( transList )

        dataframe = pandas.DataFrame( [ [ datetime.datetime(2020, 10,  5, 12, 0, 0), 10.0 ],
                                        [ datetime.datetime(2020, 10, 10, 12, 0, 0), 12.0 ]
                                        ], columns=[ 't', 'c' ] )

        indexList = data.matchStockAfter( dataframe )
        self.assertEqual( indexList, [1, 1, 0] )

    def test_calculateValueHistory(self):
        data = TransHistory()

        ## reverse order (amount, unit_price, commission, trans time)
        transList = \
            [ ( 100, 3.0, 0.0, datetime.datetime(2020, 10, 11, 12, 0, 0)),
              ( 100, 2.0, 0.0, datetime.datetime(2020, 10, 8, 12, 0, 0)),
              ( 100, 1.0, 0.0, datetime.datetime(2020, 10, 4, 12, 0, 0)) ]

        data.appendList( transList )

        dataframe = pandas.DataFrame( [ [ datetime.datetime(2020, 10,  5, 12, 0, 0), 10.0 ],
                                        [ datetime.datetime(2020, 10, 10, 12, 0, 0), 12.0 ]
                                        ], columns=[ 't', 'c' ] )

        valueFrame = data.calculateValueHistory( dataframe )
        self.assertTrue( valueFrame is not None )
        self.assertEqual( valueFrame.empty, False )

        self.assertEqual( valueFrame.at[0, "t"], pandas.Timestamp('2020-10-05 12:00:00') )
        self.assertEqual( valueFrame.at[0, "c"], 2000.0 )

        self.assertEqual( valueFrame.at[1, "t"], pandas.Timestamp('2020-10-10 12:00:00') )
        self.assertEqual( valueFrame.at[1, "c"], 3600.0 )

    def test_matchTransactionsFirst01(self):
        data = TransHistory()

        ## reverse order
        transList = \
            [ ( -200, 3.5, 0.1, datetime.datetime(2020, 10, 5, 15, 41, 33)),
              (  300, 2.0, 0.1, datetime.datetime(2020, 9, 25, 13, 11, 31)),
              (  200, 3.0, 0.1, datetime.datetime(2020, 8, 31,  9, 11, 26)),
              (  100, 4.0, 0.1, datetime.datetime(2020, 8, 25, 13, 11, 31)) ]

        data.appendList( transList )

        self.assertEqual( data.currentAmount(), 400 )

        transList: TransactionsMatch = data.matchTransactionsFirst()
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
            [ ( -40, 5.0, 0.4, datetime.datetime(2020, 10, 5, 15, 41, 33)),
              (  30, 3.0, 0.3, datetime.datetime(2020, 9, 25, 13, 11, 31)),
              (  20, 4.0, 0.2, datetime.datetime(2020, 8, 31,  9, 11, 26)),
              (  20, 2.0, 0.2, datetime.datetime(2020, 8, 25, 13, 11, 31)) ]

        data.appendList( transList )

        self.assertEqual( data.currentAmount(), 30 )

        gainValue = data.transactionsGain( matchMode, False )
        self.assertEqual( gainValue, 100.0 )                     ## 20*3 + 20*2

        gainValue = data.transactionsGain( matchMode, True )
        self.assertEqual( gainValue, 99.19999999999999 )
