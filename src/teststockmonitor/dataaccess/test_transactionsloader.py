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
import codecs
# import pandas

from teststockmonitor.data import get_data_path
from stockmonitor.dataaccess.transactionsloader import parse_mb_transactions_data


## =================================================================


class TransactionsLoaderTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_parse_mb_transactions_data_valid(self):
        transactionsPath = get_data_path( "transactions_valid.csv" )
        with codecs.open(transactionsPath, 'r', encoding='utf-8', errors='replace') as srcFile:
            dataFrame = parse_mb_transactions_data( srcFile )

        self.assertEqual( dataFrame["currency"][0], "PLN" )
        self.assertEqual( dataFrame["unit_price"][1], 3.288 )

    def test_parse_mb_transactions_data_badseparator(self):
        transactionsPath = get_data_path( "transactions_bad_separator.csv" )
        with codecs.open(transactionsPath, 'r', encoding='utf-8', errors='replace') as srcFile:
            dataFrame = parse_mb_transactions_data( srcFile )

        self.assertEqual( dataFrame["currency"][0], "PLN" )
        self.assertEqual( dataFrame["unit_price"][1], 18.95 )
