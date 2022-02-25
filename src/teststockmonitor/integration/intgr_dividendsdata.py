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

import sys
import logging

from stockmonitor.dataaccess.dividendsdata import DividendsCalendarData


_LOGGER = logging.getLogger(__name__)


logging.basicConfig( level=logging.DEBUG )


failed_counter = 0


_LOGGER.info( "loading worksheet" )

dataAccess = DividendsCalendarData()
dataAccess.loadWorksheet()

frame = dataAccess.dao.storage.worksheet
if frame is None:
    failed_counter += 1
    _LOGGER.warning( "" )
    _LOGGER.warning( "unable to load data" )
    _LOGGER.warning( "" )
else:
    _LOGGER.info( "loaded data:\n%s", frame )
    _LOGGER.info( "loaded data size: %s", frame.shape )
    if frame.shape != (30, 8):
        failed_counter += 1
        _LOGGER.warning( "unexpected data size" )


if failed_counter > 0:
    _LOGGER.warning( "failed tests: %s", failed_counter )
    sys.exit( 1 )