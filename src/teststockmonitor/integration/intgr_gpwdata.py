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

from stockmonitor.dataaccess.gpw.gpwdata import GpwIndicatorsData


class CheckGpwData( unittest.TestCase ):

    def test_indicators( self ):
        stockAccess = GpwIndicatorsData()
        stockAccess.loadWorksheet()

        frame = stockAccess.dao.storage.worksheet
        self.assertIsNotNone( frame )
        self.assertEqual( frame.shape, (427, 12), f"loaded data:\n{frame}" )


## ==============================================================


if __name__ == '__main__':
    unittest.main()
