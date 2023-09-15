#!/usr/bin/env python3
#
# MIT License
#
# Copyright (c) 2023 Arkadiusz Netczuk <dev.arnet@gmail.com>
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

import sys
import os
import logging
import datetime
import argparse

from stockmonitor.dataaccess.transactionsloader import load_mb_transactions
from stockmonitor.datatypes.datacontainer import DataContainer
from stockmonitor.datatypes.datatypes import TransactionMatchMode

# from dateutil.rrule import rrule, DAILY
#
# from pandas.core.frame import DataFrame
#
# from stockdataaccess.io import read_dict
# from stockdataaccess.persist import store_object_simple


_LOGGER = logging.getLogger(__name__)


def process_transactions_history( trans_hist_path: str, out_trans_path: str ) -> bool:
    _LOGGER.info( "opening transactions history: %s", trans_hist_path )

    imported_data, data_type = load_mb_transactions( trans_hist_path )
    if imported_data is None:
        _LOGGER.error( "unable to import data from %s", data_type )
        return False

    if data_type != 0:
        _LOGGER.error( "given data type not supported: %s", data_type )
        return False

    data_container = DataContainer()
    data_container.userContainer.transactionsMatchMode = TransactionMatchMode.OLDEST
    data_container.importWalletTransactions( imported_data, False )

    trans_data = data_container.getWalletSellTransactions()
    _LOGGER.info( "transactions:\n%s", trans_data )

    if out_trans_path:
        if out_trans_path.endswith('.json'):
            trans_data.to_json( out_trans_path, orient="records" )
        elif out_trans_path.endswith('.xls'):
            trans_data.to_excel( out_trans_path )
        elif out_trans_path.endswith('.xlsx'):
            trans_data.to_excel( out_trans_path )
        #elif out_trans_path.endswith('.csv'):
        else:
            trans_data.to_csv( out_trans_path, sep=';', encoding='utf-8' )
        _LOGGER.info( "transactions stored to file %s", out_trans_path )

    return True


def extract_buysell( args ):
    return process_transactions_history( args.transhistory, args.trans_out_file )


## ===================================================================


def extract_current( args ):
    trans_hist_path = args.transhistory
    out_trans_path = args.trans_out_file

    _LOGGER.info( "opening transactions history: %s", trans_hist_path )

    imported_data, data_type = load_mb_transactions( trans_hist_path )
    if imported_data is None:
        _LOGGER.error( "unable to import data from %s", data_type )
        return False

    if data_type != 0:
        _LOGGER.error( "given data type not supported: %s", data_type )
        return False

    data_container = DataContainer()
    data_container.userContainer.transactionsMatchMode = TransactionMatchMode.OLDEST
    data_container.importWalletTransactions( imported_data, False )

    trans_data = data_container.getWalletStock(show_soldout=True)
    _LOGGER.info( "transactions:\n%s", trans_data )

    if out_trans_path:
        if out_trans_path.endswith('.json'):
            trans_data.to_json( out_trans_path, orient="records" )
        elif out_trans_path.endswith('.xls'):
            trans_data.to_excel( out_trans_path )
        elif out_trans_path.endswith('.xlsx'):
            trans_data.to_excel( out_trans_path )
        #elif out_trans_path.endswith('.csv'):
        else:
            trans_data.to_csv( out_trans_path, sep=';', encoding='utf-8' )
        _LOGGER.info( "transactions stored to file %s", out_trans_path )

    return True


## ===================================================================
## ===================================================================


def main():
    parser = argparse.ArgumentParser(description='stock data grabber')
    parser.add_argument( '-la', '--logall', action='store_true', help='Log all messages' )

    subparsers = parser.add_subparsers( help='extract mode', description="select one of subcommands", dest='subcommand', required=True )

    ## =================================================

    subparser = subparsers.add_parser('buysell', help='Extract buy and matched sell transactions')
    subparser.set_defaults( func=extract_buysell )
    subparser.add_argument( '-th', '--transhistory', action='store', help='Path to file with history of transactions' )
    subparser.add_argument( '--trans_out_file', action='store', help='Path to file with transactions (supported .json, .xls, .xlsx, .csv extensions)' )

    ## =================================================

    subparser = subparsers.add_parser('current', help='Extract current state of wallet')
    subparser.set_defaults( func=extract_current )
    subparser.add_argument( '-th', '--transhistory', action='store', help='Path to file with history of transactions' )
    subparser.add_argument( '--trans_out_file', action='store', help='Path to file with transactions (supported .json, .xls, .xlsx, .csv extensions)' )

    ## =================================================

    args = parser.parse_args()

    logging.basicConfig()
    if args.logall is True:
        logging.getLogger().setLevel( logging.DEBUG )
    else:
        logging.getLogger().setLevel( logging.INFO )

    if "func" not in args:
        ## no command given
        return os.EX_USAGE

    _LOGGER.info( "starting data extraction" )

    succeed = args.func( args )

    if not succeed:
        _LOGGER.info( "unable to process data" )
        return os.EX_DATAERR

    _LOGGER.info( "processing completed" )
    return os.EX_OK


if __name__ == '__main__':
    exit_code = main()
    sys.exit( exit_code )
