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

import logging

from stockmonitor.dataaccess.shortsellingsdata import CurrentShortSellingsData,\
    HistoryShortSellingsData


_LOGGER = logging.getLogger(__name__)


logging.basicConfig( level=logging.DEBUG )


def check_current():
    _LOGGER.info( "loading worksheet" )
    
    dataAccess = CurrentShortSellingsData()
    
    dataAccess.loadWorksheet()
    
    frame = dataAccess.dao.storage.worksheet
    if frame is None:
        _LOGGER.warning( "" )
        _LOGGER.warning( "unable to load data" )
        _LOGGER.warning( "" )
    else:    
        _LOGGER.info( "loaded data:\n%s", frame )


def check_history():
    _LOGGER.info( "loading worksheet" )
    
    dataAccess = HistoryShortSellingsData()
    
    dataAccess.loadWorksheet()
    
    frame = dataAccess.dao.storage.worksheet
    if frame is None:
        _LOGGER.warning( "" )
        _LOGGER.warning( "unable to load data" )
        _LOGGER.warning( "" )
    else:    
        _LOGGER.info( "loaded data:\n%s", frame )


## =============

check_current()
check_history()
