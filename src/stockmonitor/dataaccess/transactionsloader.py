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

import logging
import tempfile
import codecs

import pandas

from stockmonitor.dataaccess.convert import convert_float, convert_int,\
    apply_on_column


_LOGGER = logging.getLogger(__name__)


def load_mb_transactions( filePath ):
    ## imported transaction values are not affected by borker's commission
    ## real sell profit is transaction value decreased by broker's commission
    ## real buy cost is transaction value increased by broker's commission
    ## broker commission: greater of 5PLN and 0.39%

    ##
    ## find line in file and remove header information leaving raw data
    ##
    headerFound  = False
    historyFound = False
    currentFound = False
    with tempfile.NamedTemporaryFile( mode='w+t' ) as tmpfile:
        with codecs.open(filePath, 'r', encoding='utf-8', errors='replace') as srcFile:
            for line in srcFile:
                if headerFound:
                    tmpfile.write(line)
                elif "Czas transakcji" in line:
                    headerFound = True
                elif "Historia transakcji" in line:
                    historyFound = True
                elif "Transakcje bie" in line:
                    currentFound = True
        tmpfile.seek(0)

        if headerFound is False:
            _LOGGER.error("unable to find data header")
            return ( None, -1 )

        importedData = parse_mb_transactions_data( tmpfile )
        ## print("importing:", importedData)

    if historyFound:
        ## load history transactions
        return ( importedData, 0 )
    if currentFound:
        ## add transactions
        return ( importedData, 1 )
    # else
    return ( None, -1 )


def parse_mb_transactions_data( sourceFile ):
    with fix_separator( sourceFile ) as tmpfile:
#         print( "file:\n" + tmpfile.read() )
#         tmpfile.seek(0)

        columns = count_separator( tmpfile, ";" )
        tmpfile.seek(0)

        header = []
        if columns == 8:
            header = [ "trans_time", "name", "stock_id", "k_s", "amount",
                       "unit_price", "unit_currency", "price", "currency" ]
        elif columns == 10:
            header = [ "trans_time", "name", "stock_id", "k_s", "amount",
                       "unit_price", "unit_currency", "commision_value", "commision_currency", "price", "currency" ]

#         print( "header:", header, columns )

        dataFrame = pandas.read_csv( tmpfile, names=header,
                                     sep=r'[;\t]', decimal='.', thousands=' ', engine='python', encoding='utf_8' )

#     print( "raw data:\n" + str( dataFrame ) )

    apply_on_column( dataFrame, 'name', str )

    #### fix names to match GPW names
    ## XTRADEBDM -> XTB
    ## CELONPHARMA -> CLNPHARMA
    dataFrame["name"].replace({"XTRADEBDM": "XTB", "CELONPHARMA": "CLNPHARMA"}, inplace=True)

    apply_on_column( dataFrame, 'amount', convert_int )

    apply_on_column( dataFrame, 'unit_price', convert_float )
    apply_on_column( dataFrame, 'price', convert_float )

    return dataFrame


def fix_separator( sourceFile ):
    # pylint: disable=R1732
    tmpfile = tempfile.NamedTemporaryFile( mode='w+t' )

#     with codecs.open(sourceFilePath, 'r', encoding='utf-8', errors='replace') as srcFile:
    for line in sourceFile:
        colonsNum = line.count( "," )
        if colonsNum == 10:
            ## example: 21.11.2020 11:22:33,ENTER,WWA-GPW,S,100,22,70,PLN,2 270,0,PLN
            line = replace_nth( line, ",", ".", 9 )
            line = replace_nth( line, ",", ".", 6 )
            line = line.replace( ",", ";" )
        elif colonsNum == 13:
            ## example: 18.10.2021 10:54:59,ENTER,WWA-GPW,K,120,12,30,PLN,5,76,PLN,1 476,0,PLN
            line = replace_nth( line, ",", ".", 12 )
            line = replace_nth( line, ",", ".", 9 )
            line = replace_nth( line, ",", ".", 6 )
            line = line.replace( ",", ";" )
        tmpfile.write(line)

    tmpfile.seek(0)
    return tmpfile


def count_separator( sourceFile, separator ):
    for line in sourceFile:
        return line.count( separator )
    return 0


## 'occurence' starts from 1
def replace_nth(stringData, sub, repl, occurence):
    find = stringData.find(sub)
    # If find is not -1 we have found at least one match for the substring
    i = find != -1
    # loop util we find the nth or we find no match
    while find != -1 and i != occurence:
        # find + 1 means we start searching from after the last match
        find = stringData.find(sub, find + 1)
        i += 1
    # If i is equal to n we found nth match so replace
    if i == occurence:
        return stringData[:find] + repl + stringData[find + len(sub):]
    return stringData
