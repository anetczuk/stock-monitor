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
# import datetime
import argparse
import pandas

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


## ===================================================================


def load_dataframe( trans_hist_path ):
    _LOGGER.info( "opening transactions history: %s", trans_hist_path )

    imported_data, data_type = load_mb_transactions( trans_hist_path )
    if imported_data is None:
        _LOGGER.error( "unable to import data from %s", data_type )
        return None

    if data_type != 0:
        _LOGGER.error( "given data type not supported: %s", data_type )
        return None

    return imported_data


def store_dataframe( trans_data, out_trans_path ):
    if not out_trans_path:
        return
    if out_trans_path.endswith('.json'):
        trans_data.to_json( out_trans_path, orient="records" )
    elif out_trans_path.endswith('.xls'):
        trans_data.to_excel( out_trans_path )
    elif out_trans_path.endswith('.xlsx'):
        # trans_data.to_excel( out_trans_path )

        sheet_name = "data"
        writer = pandas.ExcelWriter(out_trans_path, engine='xlsxwriter')        # pylint: disable=abstract-class-instantiated
        trans_data.to_excel(writer, sheet_name=sheet_name, index=False)         # send df to writer
        worksheet = writer.sheets[sheet_name]                                   # pull worksheet object
        for idx, col in enumerate(trans_data):                                  # loop through all columns
            series = trans_data[col]
            max_len = max(( series.astype(str).map(len).max(),  # len of largest item
                            len(str(series.name))               # len of column name/header
                            )
                          ) + 1  # adding a little extra space
            worksheet.set_column(idx, idx, max_len)  # set column width
        writer.save()

    #elif out_trans_path.endswith('.csv'):
    else:
        trans_data.to_csv( out_trans_path, sep=';', encoding='utf-8' )
    _LOGGER.info( "transactions stored to file %s", out_trans_path )


def import_data( trans_hist_path ):
    imported_data = load_dataframe( trans_hist_path )
    if imported_data is None:
        return None

    data_container = DataContainer()
    data_container.userContainer.transactionsMatchMode = TransactionMatchMode.OLDEST
    data_container.importWalletTransactions( imported_data, False )

    return data_container


## ===================================================================


def extract_buysell( args ):
    trans_hist_path = args.transhistory
    out_trans_path = args.trans_out_file

    data_container: DataContainer = import_data( trans_hist_path )
    if data_container is None:
        return False

    trans_data = data_container.getWalletSellTransactions()
    _LOGGER.info( "transactions:\n%s", trans_data )

    store_dataframe( trans_data, out_trans_path )
    return True


## ===================================================================


def extract_current( args ):
    trans_hist_path = args.transhistory
    out_trans_path = args.trans_out_file

    data_container: DataContainer = import_data( trans_hist_path )
    if data_container is None:
        return False

    trans_data = data_container.getWalletStock(show_soldout=True)
    _LOGGER.info( "transactions:\n%s", trans_data )

    store_dataframe( trans_data, out_trans_path )
    return True


## ===================================================================


def extract_currentbuy( args ):
    trans_hist_path = args.transhistory
    out_trans_path = args.trans_out_file

    data_container: DataContainer = import_data( trans_hist_path )
    if data_container is None:
        return False

    trans_data = data_container.getWalletBuyTransactions(sort_data=True)
    _LOGGER.info( "transactions:\n%s", trans_data )

    store_dataframe( trans_data, out_trans_path )
    return True


## ===================================================================


def extract_walletvaluehistory( args ):
    trans_hist_path = args.transhistory
    out_path = args.out_file

    data_container: DataContainer = import_data( trans_hist_path )
    if data_container is None:
        return False

    _LOGGER.info( "preparing wallet value history" )
    ticker_list = None
    values_data = data_container.getWalletValueHistory( "MAX", ticker_list )
    _LOGGER.info( "values:\n%s", values_data )

    store_dataframe( values_data, out_path )
    return True


## ===================================================================


def extract_walletprofithistory( args ):
    trans_hist_path = args.transhistory
    out_path = args.out_file
    calc_overall = args.overall

    data_container: DataContainer = import_data( trans_hist_path )
    if data_container is None:
        return False

    _LOGGER.info( "preparing wallet profit history" )
    ticker_list = None
    values_data = data_container.getWalletProfitHistory( "MAX", calculateOverall=calc_overall, tickerList=ticker_list )
    _LOGGER.info( "values:\n%s", values_data )

    store_dataframe( values_data, out_path )
    return True


## ===================================================================
## ===================================================================


def main():
    parser = argparse.ArgumentParser(description='stock data grabber')
    parser.add_argument( '-la', '--logall', action='store_true', help='Log all messages' )
    parser.add_argument( '--listtools', action='store_true', help='List tools' )

    subparsers = parser.add_subparsers( help='extract mode', description="select one of subcommands",
                                        dest='subcommand', required=False )

    ## =================================================

    subparser = subparsers.add_parser('buysell', help='Extract buy and matched sell transactions')
    subparser.set_defaults( func=extract_buysell )
    subparser.add_argument( '-th', '--transhistory', action='store', help='Path to file with history of transactions' )
    subparser.add_argument( '--trans_out_file', action='store',
                            help='Path to file with transactions (supported .json, .xls, .xlsx, .csv extensions)' )

    ## =================================================

    subparser = subparsers.add_parser('current', help='Extract current state of wallet')
    subparser.set_defaults( func=extract_current )
    subparser.add_argument( '-th', '--transhistory', action='store', help='Path to file with history of transactions' )
    subparser.add_argument( '--trans_out_file', action='store',
                            help='Path to file with transactions (supported .json, .xls, .xlsx, .csv extensions)' )

    ## =================================================

    subparser = subparsers.add_parser('currentbuy', help='Extract list of current buy transactions')
    subparser.set_defaults( func=extract_currentbuy )
    subparser.add_argument( '-th', '--transhistory', action='store', help='Path to file with history of transactions' )
    subparser.add_argument( '--trans_out_file', action='store',
                            help='Path to file with transactions (supported .json, .xls, .xlsx, .csv extensions)' )

    ## =================================================

    subparser = subparsers.add_parser('walletvaluehistory', help='Extract history of wallet value')
    subparser.set_defaults( func=extract_walletvaluehistory )
    subparser.add_argument( '-th', '--transhistory', action='store', help='Path to file with history of transactions' )
    subparser.add_argument( '--out_file', action='store',
                            help='Path to file with output (supported .json, .xls, .xlsx, .csv extensions)' )

    ## =================================================

    subparser = subparsers.add_parser('walletprofithistory', help='Extract history of wallet profit')
    subparser.set_defaults( func=extract_walletprofithistory )
    subparser.add_argument( '-th', '--transhistory', action='store', help='Path to file with history of transactions' )
    subparser.add_argument( '--overall', action='store_true', help='Include gain of sold transactions' )
    subparser.add_argument( '--out_file', action='store',
                            help='Path to file with output (supported .json, .xls, .xlsx, .csv extensions)' )

    ## =================================================

    args = parser.parse_args()

    if args.listtools is True:
        tools_list = list( subparsers.choices.keys() )
        print( ", ".join( tools_list ) )
        return

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
