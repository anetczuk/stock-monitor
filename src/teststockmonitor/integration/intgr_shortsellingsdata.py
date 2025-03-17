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

import logging

from stockdataaccess.dataaccess.shortsellingsdata import CurrentShortSellingsData, \
    HistoryShortSellingsData


_LOGGER = logging.getLogger(__name__)


# logging.basicConfig( level=logging.DEBUG )


class CheckShortSelling( unittest.TestCase ):

    def test_current( self ):
        dataAccess = CurrentShortSellingsData()
        dataAccess.loadWorksheet()

        frame = dataAccess.dao.storage.worksheet
        self.assertIsNotNone( frame )
        self.assertEqual( (22, 6), frame.shape, f"loaded data:\n{frame}" )

    def test_history( self ):
        dataAccess = HistoryShortSellingsData()
        dataAccess.loadWorksheet()

        frame = dataAccess.dao.storage.worksheet
        self.assertIsNotNone( frame )
        self.assertEqual( (200, 6), frame.shape, f"loaded data:\n{frame}" )


## ==============================================================


if __name__ == '__main__':
    unittest.main()
