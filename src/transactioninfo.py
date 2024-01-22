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
from pandas.core.frame import DataFrame

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


def store_dataframe( trans_data: DataFrame, out_trans_path, description="" ):
    if not out_trans_path:
        return

    numpy_data_list = []

    if description:
        desc_dict = {"description": [description]}
        description_frame = DataFrame.from_dict(desc_dict)
        numpy_data_list.append(description_frame)

    numpy_data_list.append(trans_data)
    store_dataframe_list(out_trans_path, numpy_data_list)

    _LOGGER.info( "transactions stored to file %s", out_trans_path )


def store_dataframe_list(out_file_path, numpy_data_list, horizontal=True):
    if out_file_path.endswith('.json'):
        with open(out_file_path, "w", encoding="utf-8") as data_file:
            # clear file content
            pass

        for numpy_data in numpy_data_list:
            with open(out_file_path, "a", encoding="utf-8") as data_file:
                numpy_data.to_json(data_file, orient="records")

    elif out_file_path.endswith('.csv'):
        with open(out_file_path, "w", encoding="utf-8") as data_file:
            # clear file content
            pass

        for numpy_data in numpy_data_list:
            # horizontal not supported
            with open(out_file_path, "a", encoding="utf-8") as data_file:
                numpy_data.to_csv(data_file, sep=";", encoding="utf-8")
            with open(out_file_path, "a", encoding="utf-8") as data_file:
                data_file.write(";\n;\n")

    elif out_file_path.endswith('.xls'):
        sheet_name = "data"
        # pylint: disable=abstract-class-instantiated
        with pandas.ExcelWriter(out_file_path, engine="openpyxl") as writer:
            start_row = 0
            start_col = 0
            for numpy_data in numpy_data_list:
                curr_row = 0
                curr_col = 0
                if horizontal:
                    curr_col = start_col
                else:
                    curr_row = start_row
                numpy_data.to_excel(writer, sheet_name=sheet_name, index=False,
                                    startrow=curr_row, startcol=curr_col)     # send df to writer
                start_row += numpy_data.shape[0] + 3
                start_col += numpy_data.shape[1] + 1

    elif out_file_path.endswith('.xlsx'):
        sheet_name = "data"
        # pylint: disable=abstract-class-instantiated
        with pandas.ExcelWriter(out_file_path, engine="xlsxwriter") as writer:
            col_width_dict = {}
            start_row = 0
            start_col = 0
            for numpy_data in numpy_data_list:
                curr_row = 0
                curr_col = 0
                if horizontal:
                    curr_col = start_col
                else:
                    curr_row = start_row
                numpy_data.to_excel(writer, sheet_name=sheet_name, index=False,
                                    startrow=curr_row, startcol=curr_col)  # send df to writer
                start_row += numpy_data.shape[0] + 3
                start_col += numpy_data.shape[1] + 1

                # resize columns to fit content
                for idx, col in enumerate(numpy_data):  # loop through all columns
                    series = numpy_data[col]
                    item_len = series.astype(str).map(len).max()  # len of largest item
                    name_len = len(str(series.name))  # len of column name/header
                    max_len = max(item_len, name_len) + 1  # adding a little extra space
                    curr_width = col_width_dict.get(curr_col + idx, 0)
                    col_width_dict[curr_col + idx] = max(max_len, curr_width)

            worksheet = writer.sheets[sheet_name]  # pull worksheet object
            for idx, width in col_width_dict.items():  # loop through all columns
                worksheet.set_column(idx, idx, width)  # set column width

    # else csv
    else:
        raise RuntimeError(f"unknown store format: {out_file_path}")


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

    trans_data: DataFrame = data_container.getWalletSellTransactions()
    _LOGGER.info( "transactions:\n%s", trans_data )

    store_dataframe( trans_data, out_trans_path, description="matched buy and sell transactions (FIFO match)" )
    return True


## ===================================================================


def extract_current( args ):
    trans_hist_path = args.transhistory
    out_trans_path = args.trans_out_file

    data_container: DataContainer = import_data( trans_hist_path )
    if data_container is None:
        return False

    trans_data: DataFrame = data_container.getWalletStock(show_soldout=True)
    _LOGGER.info( "transactions:\n%s", trans_data )

    store_dataframe( trans_data, out_trans_path,
                     description="summary of current amounts of stock with sold-out stocks" )
    return True


## ===================================================================


def extract_currentbuy( args ):
    trans_hist_path = args.transhistory
    out_trans_path = args.trans_out_file

    data_container: DataContainer = import_data( trans_hist_path )
    if data_container is None:
        return False

    trans_data: DataFrame = data_container.getWalletBuyTransactions(sort_data=True)
    _LOGGER.info( "transactions:\n%s", trans_data )

    store_dataframe( trans_data, out_trans_path, description="list of current buy transactions (not sold)" )
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
    values_data: DataFrame = data_container.getWalletValueHistory( "MAX", ticker_list )
    _LOGGER.info( "values:\n%s", values_data )

    store_dataframe( values_data, out_path, description="history of value (capitalization) of wallet" )
    return True


## ===================================================================


def extract_walletgainhistory( args ):
    trans_hist_path = args.transhistory
    out_path = args.out_file

    data_container: DataContainer = import_data( trans_hist_path )
    if data_container is None:
        return False

    _LOGGER.info( "preparing wallet gain history" )
    values_data: DataFrame = data_container.getWalletGainHistory( "MAX" )
    _LOGGER.info( "values:\n%s", values_data )

    store_dataframe( values_data, out_path, description="history of gain (saldo of sell transactions)" )
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
    values_data: DataFrame = data_container.getWalletProfitHistory( "MAX", calculateOverall=calc_overall,
                                                                    tickerList=ticker_list )
    _LOGGER.info( "values:\n%s", values_data )

    if calc_overall:
        description = "history of overall profit (saldo of sells and capitalization of wallet"
    else:
        description = "history of saldo of wallet"
    store_dataframe( values_data, out_path, description=description )
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

    subparser = subparsers.add_parser('walletgainhistory', help='Extract history of wallet gain of sold stock')
    subparser.set_defaults( func=extract_walletgainhistory )
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
        return os.EX_OK

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
