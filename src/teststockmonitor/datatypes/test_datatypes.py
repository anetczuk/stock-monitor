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

import pickle

from stockmonitor.datatypes.datatypes import \
    MarkersContainer, MarkerEntry, FavData


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


class MarkersContainerTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_deleteItemsList(self):
        data = MarkersContainer()
        data.add( "XXX", 3.0, 100, MarkerEntry.OperationType.BUY, "red" )
        data.add( "YYY", 3.0, 100, MarkerEntry.OperationType.BUY, "green" )

        removeList = [ data.get( 1 ) ]
        data.deleteItemsList( removeList )
        self.assertEqual( data.size(), 1 )
        self.assertEqual( data.get(0).ticker, "XXX" )

    def test_getBestMatchingColor_empty(self):
        data = MarkersContainer()
        self.assertEqual( data.getBestMatchingColor( "XXX", 2.0 ), None )

    def test_getBestMatchingColor_ticker(self):
        data = MarkersContainer()
        data.add( "XXX", 3.0, 100, MarkerEntry.OperationType.BUY, "red" )
        data.add( "YYY", 3.0, 100, MarkerEntry.OperationType.BUY, "green" )

        self.assertEqual( data.getBestMatchingColor( "XXX", 2.0 ), "red" )

    def test_getBestMatchingColor_value_None(self):
        data = MarkersContainer()
        data.add( "XXX", None, 100, MarkerEntry.OperationType.BUY, "red" )

        self.assertEqual( data.getBestMatchingColor( "XXX", 2.0 ), None )

    def test_getBestMatchingColor_value_buy(self):
        data = MarkersContainer()
        data.add( "XXX", 3.0, 100, MarkerEntry.OperationType.BUY, "red" )
        data.add( "XXX", 1.0, 100, MarkerEntry.OperationType.BUY, "green" )

        self.assertEqual( data.getBestMatchingColor( "XXX", 2.0 ), "red" )

    def test_getBestMatchingColor_value_sell(self):
        data = MarkersContainer()
        data.add( "XXX", 3.0, 100, MarkerEntry.OperationType.SELL, "red" )
        data.add( "XXX", 1.0, 100, MarkerEntry.OperationType.SELL, "green" )

        self.assertEqual( data.getBestMatchingColor( "XXX", 2.0 ), "green" )

    def test_getBestMatchingColor_better_buy(self):
        data = MarkersContainer()
        data.add( "XXX", 3.0, 100, MarkerEntry.OperationType.BUY, "red" )
        data.add( "XXX", 1.0, 100, MarkerEntry.OperationType.BUY, "green" )

        self.assertEqual( data.getBestMatchingColor( "XXX", 0.5 ), "green" )

    def test_getBestMatchingColor_better_sell(self):
        data = MarkersContainer()
        data.add( "XXX", 1.0, 100, MarkerEntry.OperationType.SELL, "red" )
        data.add( "XXX", 3.0, 100, MarkerEntry.OperationType.SELL, "green" )

        self.assertEqual( data.getBestMatchingColor( "XXX", 5.0 ), "green" )

    def test_getBestMatchingColor_buy_sell(self):
        data = MarkersContainer()
        data.add( "XXX", 3.0, 100, MarkerEntry.OperationType.BUY, "red" )
        data.add( "XXX", 1.0, 100, MarkerEntry.OperationType.SELL, "green" )

        self.assertEqual( data.getBestMatchingColor( "XXX", 2.5 ), "green" )
