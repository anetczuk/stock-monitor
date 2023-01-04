#!/usr/bin/env python3
##
##
##

try:
    ## following import success only when file is directly executed from command line
    ## otherwise will throw exception when executing as parameter for "python -m"
    # pylint: disable=W0611
    import __init__
except ImportError:
    ## when import fails then it means that the script was executed indirectly
    ## in this case __init__ is already loaded
    pass

import unittest

from stockdataaccess.dataaccess.gpw.gpwcurrentdata import GpwCurrentStockData,\
    GpwCurrentIndexesData


class CheckGpwCurrentData( unittest.TestCase ):

    def test_currentstock(self):
        stockAccess = GpwCurrentStockData()
        stockAccess.loadWorksheet()

        frame = stockAccess.dao.storage.worksheet
        self.assertIsNotNone( frame )
        self.assertEqual( frame.shape, (397, 26), f"loaded data:\n{frame}" )

    def test_indexesstock(self):
        indexAccess = GpwCurrentIndexesData()
        indexAccess.loadWorksheet()

        frame = indexAccess.dao.getDataFrame()
        self.assertIsNotNone( frame )
        self.assertEqual( frame.shape, (27, 13), f"loaded data:\n{frame}" )


## ==============================================================


if __name__ == '__main__':
    unittest.main()
