# MIT License
#
# Copyright (c) 2020 Arkadiusz Netczuk <dev.arnet@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import re
import datetime
import logging


_LOGGER = logging.getLogger(__name__)


def convert_int( data ):
    if isinstance( data, int ):
        return data
    if isinstance( data, float ):
        return data
    value = data.strip()
    value = re.sub(r'\s+', '', value)       ## remove whitespaces
    try:
        return int(value)
    except ValueError:
        return value


def convert_float( data ):
    if isinstance( data, float ):
        return data
    if isinstance( data, int ):
        return data
    value = data.strip()
    value = value.replace(',', '.')
    value = re.sub(r'\s+', '', value)       ## remove whitespaces
    try:
        return float(value)
    except ValueError:
        ## _LOGGER.error( "unable to convert to float: %s %s", value, type(value) )
        return value


def convert_percentage( data ):
    if isinstance( data, float ):
        return data
    if isinstance( data, int ):
        return data
    value = data.strip()
    value = value.replace(',', '.')
    value = re.sub(r'\s+', '', value)       ## remove whitespaces
    value = value.replace('%', '')
    try:
        return float(value)
    except ValueError:
        return value


def convert_timestamp_datetime( timestamp ):
    return datetime.datetime.fromtimestamp( timestamp )


def is_numeric( value ):
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return True
    if isinstance(value, str):
        return value.isnumeric()
    return str(value).isnumeric()


class NumericFilter():

    def __eq__(self, other):
        return is_numeric( other )

    def __contains__(self, item):
        return is_numeric( item )


def filter_numeric( dataFrame, columnName ):
    numeric_filter = NumericFilter()
    return dataFrame[ dataFrame[ columnName ] == numeric_filter ]


def convert_to_float( dataFrame, columnName ):
    apply_on_column( dataFrame, columnName, convert_float )
    return filter_numeric( dataFrame, columnName )


def apply_on_column( dataFrame, columnName, function ):
    dataFrame[ columnName ] = dataFrame[ columnName ].apply( function )


def cleanup_column(dataFrame, colName):
    cleanup_column_str( dataFrame, colName, " " )
    cleanup_column_str( dataFrame, colName, "\t" )
    cleanup_column_str( dataFrame, colName, "\u00A0" )          ## non-breaking space
    cleanup_column_str( dataFrame, colName, "\xc2\xa0" )        ## non-breaking space


def cleanup_column_str(dataFrame, colName, substr):
    val = dataFrame.loc[ dataFrame[ colName ].str.contains( substr ), colName ]
    for index, value in val.items():
        val[ index ] = value.split( substr )[0]
    dataFrame.loc[ dataFrame[ colName ].str.contains( substr ), colName ] = val
