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

from stockdataaccess.dataaccess import download_html_content


if __name__ == '__main__':

    ##
    ## get information about request
    ##

    url = "https://httpbin.org/anything"
    response = download_html_content( url, None )
    print( response )
