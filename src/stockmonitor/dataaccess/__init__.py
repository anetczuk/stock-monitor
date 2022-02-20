##
##
##

import os
import logging
import pprint

import urllib
from urllib import request
import ssl
import requests

import pycurl
from io import BytesIO
from http import HTTPStatus
# import wget


script_dir = os.path.dirname(os.path.realpath(__file__))

tmp_dir = os.path.abspath( script_dir + "/../../../tmp/" ) + "/"


_LOGGER = logging.getLogger(__name__)


# ## old implementation
# def retrieve_url_urlopen( url, outputPath ):
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


# pylint: disable=W0613
def set_raise( response, *args, **kwargs ):
    response.raise_for_status()


def init_session():
    currSession = requests.Session()

    ## changed "user-agent" fixes blocking by server
    headers = {}
    headers[ "User-Agent" ] = "Mozilla/5.0 (X11; Linux x86_64)"
    currSession.headers.update( headers )

    ## raise HTTP status code
    currSession.hooks["response"] = [ set_raise ]

    return currSession


def access_url_list( session, url_list ):
    content_data = None

    for url in url_list:
        _LOGGER.debug( "requesting url: %s", url )
        result = session.get( url )
        result.raise_for_status()
        content_data = result.content

    return content_data


def retrieve_url_session( url, outputPath ):
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


## =========================================================


class CUrlConnectionRAII(object):

    def __init__(self):
        self.connection = pycurl.Curl()
        
    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()


def retrieve_url_pycurl( url, outputPath ):
    b_obj = BytesIO()
    
    with CUrlConnectionRAII() as crl:
#         crl.setopt(pycurl.USERAGENT, "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36" )
#         crl.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0" )
#         crl.setopt(pycurl.USERAGENT, "Mozilla/5.0 (X11; Linux x86_64)" )
        # Set URL value
        crl.setopt(pycurl.URL, url)
        
        # Write bytes that are utf-8 encoded
        crl.setopt(pycurl.WRITEDATA, b_obj)
        
        # Perform a file transfer 
        crl.perform()
        
        resp_code = crl.getinfo( pycurl.RESPONSE_CODE )
        if resp_code != 200:
            message = HTTPStatus( resp_code ).phrase
#             _LOGGER.info( "error code: %s: %s", resp_code, message )
            raise urllib.error.HTTPError( url, resp_code, message, None, None )
        
    # Get the content stored in the BytesIO object (in byte characters) 
    get_body = b_obj.getvalue()
    
    try:
        with open(outputPath, 'wb') as of:
            of.write( get_body )
    except UnicodeDecodeError as ex:
        _LOGGER.exception( "unable to access: %s %s", url, ex, exc_info=False )
        raise
    
    return get_body.decode('utf8')


# def retrieve_url_wget( url, outputPath ):
#     out_file_path = wget.download( url, out=outputPath, bar=None )
#     with open( out_file_path, 'r', encoding="utf-8" ) as out_file:
#         return out_file.read()


def retrieve_url_syswget( url, outputPath ):
#     wget_command = "wget -q -O " + outputPath + " '" + url + "'"
    wget_command = "wget -O " + outputPath + " '" + url + "'"
    _LOGGER.debug( "calling wget: %s", wget_command )
    os.system( wget_command )

    with open( outputPath, 'r', encoding="utf-8" ) as out_file:
        return out_file.read()


## =========================================================


retrieve_url = retrieve_url_pycurl

## unable to easily get http response codes
# retrieve_url = retrieve_url_syswget

### causes 104 error
# retrieve_url = retrieve_url_wget
# retrieve_url = retrieve_url_session
# retrieve_url = retrieve_url_urlopen


## =========================================================


def download_html_content( url, outputPath ):
    try:
        return retrieve_url( url, outputPath )

    except urllib.error.HTTPError:
        _LOGGER.exception( "exception when accessing: %s", url, exc_info=False )
        raise
    except urllib.error.URLError as ex:
        _LOGGER.exception( "unable to access: %s %s", url, ex, exc_info=False )
        raise
    except ConnectionResetError as ex:
        _LOGGER.exception( "unable to access -- connection reset: %s %s", url, ex, exc_info=False )
        raise


def download_html_content_list( url_list, outputPath ):
    return retrieve_url_list( url_list, outputPath )

#     try:
#         return retrieve_url_list( url_list, outputPath )
#
#     except urllib.error.HTTPError:
#         _LOGGER.exception( "exception when accessing: %s", url_list[-1], exc_info=False )
#         raise
#     except urllib.error.URLError as ex:
#         _LOGGER.exception( "unable to access: %s %s", url_list[-1], ex, exc_info=False )
#         raise
#     except ConnectionResetError as ex:
#         _LOGGER.exception( "unable to access -- connection reset: %s %s", url_list[-1], ex, exc_info=False )
#         raise
