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
# import datetime
import pandas

from stockmonitor.analysis.stockanalysisdata import VarCalc


## =================================================================


class VarCalcTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_calcVar(self):
        dataColumn1 = pandas.Series( [10.0, 10.5, 10.0, 10.5] )
        dataColumn2 = pandas.Series( [10.0, 11.0, 10.0, 11.0] )
        change1 = VarCalc.calcVar( dataColumn1 )
        change2 = VarCalc.calcVar( dataColumn2 )
        self.assertGreater(change2, change1)

    def test_calcChange1(self):
        dataColumn1 = pandas.Series( [10.0, 10.5, 10.0, 10.5] )
        dataColumn2 = pandas.Series( [10.0, 11.0, 10.0, 11.0] )
        change1 = VarCalc.calcChange1( dataColumn1 )
        change2 = VarCalc.calcChange1( dataColumn2 )
        self.assertGreater(change2, change1)

    def test_calcChange3(self):
        dataColumn = pandas.Series( [10.0, 15.0] )
        change = VarCalc.calcChange3( dataColumn, 20.0 )
        self.assertEqual( change, (50.0, 1) )

        dataColumn = pandas.Series( [10.0, 15.0, 16.0] )
        change = VarCalc.calcChange3( dataColumn, 20.0 )
        self.assertEqual( change, (60.0, 1) )

        dataColumn = pandas.Series( [10.0, 7.5, 15.0] )
        change = VarCalc.calcChange3( dataColumn, 20.0 )
        self.assertEqual(change, (100.0, 1))

        dataColumn = pandas.Series( [10.0, 11.0, 15.0, 14.0] )
        change = VarCalc.calcChange3( dataColumn, 20.0 )
        self.assertEqual(change, (50.0, 1))

        dataColumn = pandas.Series( [10.0, 7.5, 15.0, 11.0] )
        change = VarCalc.calcChange3( dataColumn, 20.0 )
        self.assertEqual(change, (100.0, 1))
