#!/usr/bin/env python3
#
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

try:
    ## following import success only when file is directly executed from command line
    ## otherwise will throw exception when executing as parameter for "python -m"
    # pylint: disable=W0611
    import __init__
except ImportError:
    ## when import fails then it means that the script was executed indirectly
    ## in this case __init__ is already loaded
    pass

import sys
import unittest

from stockdataaccess.dataaccess.shortsellingsdata import HistoryShortSellingsData


# class CurrentShortSellingsDataTest(unittest.TestCase):
#
#     def setUp(self):
#         ## Called before testfunction is executed
#         pass
#
#     def tearDown(self):
#         ## Called after testfunction was executed
#         pass
#
#     def test_access(self):
#         dataAccess = CurrentShortSellingsData()
#         dataframe  = dataAccess.loadWorksheet()
#         self.assertTrue( dataframe is not None )
#         print( f"dataframe:\n{dataframe}" )


class HistoryShortSellingsDataTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_access(self):
        dataAccess = HistoryShortSellingsData()
        dataframe  = dataAccess.loadWorksheet()
        self.assertTrue( dataframe is not None )
        print( f"dataframe:\n{dataframe}" )


## ============================= main section ===================================


if __name__ == '__main__':
    curr_module = sys.modules[__name__]
    suites = unittest.defaultTestLoader.loadTestsFromModule( curr_module )
    test_suite = unittest.TestSuite(suites)
    unittest.TextTestRunner().run(test_suite)
