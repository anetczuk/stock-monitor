import os
import logging

import urllib.request as request
import ssl


script_dir = os.path.dirname(os.path.realpath(__file__))

tmp_dir = os.path.abspath( script_dir + "/../../../tmp/" ) + "/"


_LOGGER = logging.getLogger(__name__)


def urlretrieve( url, outputPath ):
    ##
    ## Under Ubuntu 20 SSL configuration has changed causing problems with SSL keys.
    ## For more details see: https://forums.raspberrypi.com/viewtopic.php?t=255167
    ##
    ctx_no_secure = ssl.create_default_context()
    ctx_no_secure.set_ciphers('HIGH:!DH:!aNULL')
    ctx_no_secure.check_hostname = False
    ctx_no_secure.verify_mode = ssl.CERT_NONE

    ## changed "user-agent" fixes blocking by server
    req = request.Request( url, headers={'User-Agent': 'Mozilla/5.0'} )
    result = request.urlopen( req, context=ctx_no_secure )

#     result = request.urlopen( url, context=ctx_no_secure )
    content_data = result.read()

    try:
        with open(outputPath, 'wb') as of:
            of.write( content_data )

#         content_text = content_data.decode("utf-8")
#         with open(outputPath, 'wt') as of:
#             of.write( content_text )

    except UnicodeDecodeError as ex:
        _LOGGER.exception( "unable to access: %s %s", url, ex, exc_info=False )
        raise

#     urllib.request.urlretrieve( url, outputPath, context=ctx_no_secure )
#     urllib.request.urlretrieve( url, outputPath )

    return content_data
