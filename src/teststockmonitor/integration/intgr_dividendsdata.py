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

from stockdataaccess.dataaccess.dividendsdata import DividendsCalendarData


class CheckDividendsCalendar( unittest.TestCase ):

    def test_load(self):
        dataAccess = DividendsCalendarData()
        dataAccess.loadWorksheet()

        frame = dataAccess.dao.storage.worksheet
        self.assertIsNotNone( frame )
        self.assertEqual( frame.shape, (37, 8), f"loaded data:\n{frame}" )


## ==============================================================


if __name__ == '__main__':
    unittest.main()
