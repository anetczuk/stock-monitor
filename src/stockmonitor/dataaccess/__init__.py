##
##
##

import os
import logging
import pprint

import urllib.request as request
import ssl
import requests


script_dir = os.path.dirname(os.path.realpath(__file__))

tmp_dir = os.path.abspath( script_dir + "/../../../tmp/" ) + "/"


_LOGGER = logging.getLogger(__name__)


# ## old implementation
# def urlretrieve( url, outputPath ):
#     ##
#     ## Under Ubuntu 20 SSL configuration has changed causing problems with SSL keys.
#     ## For more details see: https://forums.raspberrypi.com/viewtopic.php?t=255167
#     ##
#     ctx_no_secure = ssl.create_default_context()
#     ctx_no_secure.set_ciphers('HIGH:!DH:!aNULL')
#     ctx_no_secure.check_hostname = False
#     ctx_no_secure.verify_mode = ssl.CERT_NONE
#
#     ## changed "user-agent" fixes blocking by server
#     headers = {}
#     headers[ "User-Agent" ] = "Mozilla/5.0 (X11; Linux x86_64)"
# #     headers[ "User-Agent" ] = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0"
#     # headers[ "User-Agent" ] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
#     req = request.Request( url, headers=headers )
#     result = request.urlopen( req, timeout=30, context=ctx_no_secure )
#
# #     result = request.urlopen( url, context=ctx_no_secure )
#     content_data = result.read()
#
#     try:
#         with open(outputPath, 'wb') as of:
#             of.write( content_data )
#
# #         content_text = content_data.decode("utf-8")
# #         with open(outputPath, 'wt') as of:
# #             of.write( content_text )
#
#     except UnicodeDecodeError as ex:
#         _LOGGER.exception( "unable to access: %s %s", url, ex, exc_info=False )
#         raise
#
# #     urllib.request.urlretrieve( url, outputPath, context=ctx_no_secure )
# #     urllib.request.urlretrieve( url, outputPath )
#
#     return content_data


## ====================================================================


def init_session():
    currSession = requests.Session()

    ## changed "user-agent" fixes blocking by server
    headers = {}
    headers[ "User-Agent" ] = "Mozilla/5.0 (X11; Linux x86_64)"
#             headers[ "User-Agent" ] = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0"
    ## headers[ "User-Agent" ] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
    currSession.headers.update( headers )

    ## raise HTTP status code
    assert_status_hook = lambda response, *args, **kwargs: response.raise_for_status()
    currSession.hooks["response"] = [assert_status_hook]

    return currSession


def access_url_list( session, url_list ):
    content_data = None

    for url in url_list:
        _LOGGER.debug( "requesting url: %s", url )
        result = session.get( url )
        result.raise_for_status()
        content_data = result.content

    return content_data


def retrieve_url( url, outputPath ):
    with init_session() as currSession:
        url_list = [ url ]
        content_data = access_url_list( currSession, url_list )

    try:
        with open(outputPath, 'wb') as of:
            of.write( content_data )

    except UnicodeDecodeError as ex:
        _LOGGER.exception( "unable to access: %s %s", url, ex, exc_info=False )
        raise

    return content_data


def retrieve_url_list( url_list, outputPath ):
    with init_session() as currSession:
        content_data = access_url_list( currSession, url_list )

    try:
        with open(outputPath, 'wb') as of:
            of.write( content_data )

    except UnicodeDecodeError as ex:
        _LOGGER.exception( "unable to access: %s %s", url_list[-1], ex, exc_info=False )
        raise

    return content_data
