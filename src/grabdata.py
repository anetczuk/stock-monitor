#!/usr/bin/env python3
#
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

import os
import logging
import datetime
import argparse

from pandas.core.frame import DataFrame

from stockdataaccess.io import read_dict
from stockdataaccess.persist import store_object_simple

from stockdataaccess.dataaccess.worksheetdata import BaseWorksheetData
from stockdataaccess.dataaccess.gpw.gpwarchivedata import GpwArchiveData
from stockdataaccess.dataaccess.gpw.gpwespidata import GpwESPIData
from stockdataaccess.dataaccess.gpw.gpwcurrentdata import GpwCurrentIndexesData,\
    GpwCurrentStockData
from stockdataaccess.dataaccess.gpw.gpwdata import GpwIsinMapData,\
    GpwIndicatorsData
from stockdataaccess.dataaccess.gpw.gpwintradaydata import GpwCurrentStockIntradayData,\
    GpwCurrentIndexIntradayData
from stockdataaccess.dataaccess.dividendsdata import DividendsCalendarData
from stockdataaccess.dataaccess.finreportscalendardata import FinRepsCalendarData,\
    PublishedFinRepsCalendarData
from stockdataaccess.dataaccess.globalindexesdata import GlobalIndexesData
from stockdataaccess.dataaccess.metastockdata import MetaStockIntradayData
from stockdataaccess.dataaccess.shortsellingsdata import CurrentShortSellingsData,\
    HistoryShortSellingsData


_LOGGER = logging.getLogger(__name__)


## ===================================================================
## ===================================================================


def grab_simple_template( GRABBER_CLASS ):
    def grab_data( args ):
        _LOGGER.debug( "executing provider: %s", GRABBER_CLASS.__name__ )
        provider: BaseWorksheetData = GRABBER_CLASS()
        store_provider_data2( provider, args.out_format, args.out_path )
        return True

    return grab_data


def grab_isin_template( GRABBER_CLASS ):
    def grab_data( args ):
        _LOGGER.debug( "executing provider: %s", GRABBER_CLASS.__name__ )
        provider: BaseWorksheetData = GRABBER_CLASS( args.isin )
        store_provider_data2( provider, args.out_format, args.out_path )
        return True

    return grab_data


def grab_date_template( GRABBER_CLASS ):
    def grab_data( args ):
        _LOGGER.debug( "executing provider: %s", GRABBER_CLASS.__name__ )
        input_date = datetime.datetime.strptime( args.date, "%Y-%m-%d").date()
        provider: BaseWorksheetData = GRABBER_CLASS( input_date )
        store_provider_data2( provider, args.out_format, args.out_path )
        return True

    return grab_data


## ===================================================================


def grab_all( args ):
    out_format = args.out_format
    if not out_format:
        ## None or empty format
        print( "out_format is required" )
        return

    out_dir = args.out_dir
    if out_dir is not None:
        os.makedirs( out_dir, exist_ok=True )

#     curr_date = datetime.date.today()

    provider: BaseWorksheetData = GpwCurrentStockData()
    store_provider_data( provider, out_format, out_dir, "gpw_curr_stock" )

    provider: BaseWorksheetData = GpwCurrentIndexesData()
    store_provider_data( provider, out_format, out_dir, "gpw_curr_indexes" )

    provider: BaseWorksheetData = GpwIsinMapData()
    store_provider_data( provider, out_format, out_dir, "gpw_isin_map" )

    provider: BaseWorksheetData = GpwIndicatorsData()
    store_provider_data( provider, out_format, out_dir, "gpw_indicators" )

    provider: BaseWorksheetData = GpwESPIData()
    store_provider_data( provider, out_format, out_dir, "gpw_espi" )

    provider: BaseWorksheetData = GpwArchiveData()
    store_provider_data( provider, out_format, out_dir, "gpw_arch_data" )

    provider: BaseWorksheetData = DividendsCalendarData()
    store_provider_data( provider, out_format, out_dir, "dividends_cal" )

    provider: BaseWorksheetData = FinRepsCalendarData()
    store_provider_data( provider, out_format, out_dir, "fin_reps_cal" )

    provider: BaseWorksheetData = PublishedFinRepsCalendarData()
    store_provider_data( provider, out_format, out_dir, "pub_fin_reps_cal" )

    provider: BaseWorksheetData = GlobalIndexesData()
    store_provider_data( provider, out_format, out_dir, "global_indexes" )

    provider: BaseWorksheetData = MetaStockIntradayData()
    store_provider_data( provider, out_format, out_dir, "metastock_intraday" )

    provider: BaseWorksheetData = CurrentShortSellingsData()
    store_provider_data( provider, out_format, out_dir, "curr_shorts" )

    provider: BaseWorksheetData = HistoryShortSellingsData()
    store_provider_data( provider, out_format, out_dir, "hist_shorts" )
    
    return True


def grab_by_config( parser, args ):
    config_path = args.config_path
    if not config_path:
        ## None or empty format
        print( "config_path is required" )
        return

    try:
        config_dict = read_dict( config_path )
    except Exception as ex:
        _LOGGER.exception( "unable to read configuration file %s, reason: %s", config_path, ex )
        return


    for mode, params in config_dict.items():
        params_list = [ mode ] + params.copy()
        _LOGGER.info( "executing mode: %s", params_list )
        mode_args = parser.parse_args( params_list )
        mode_args.func( mode_args )

    return True


## ===================================================================


def store_provider_data( provider: BaseWorksheetData, out_format, out_dir, out_file_name ):
    out_path = None
    if out_dir is not None:
        file_name = f"{out_file_name}.{out_format}"
        out_path  = os.path.join( out_dir, file_name )
    store_provider_data2( provider, out_format, out_path )


def store_provider_data2( provider: BaseWorksheetData, out_format, out_path ):
    dataframe: DataFrame = provider.accessWorksheetData()
    store_dataframe( dataframe, out_format, out_path )


def store_dataframe( dataframe: DataFrame, out_format, out_path ):
    if dataframe is None:
        _LOGGER.error( "unable to grab data" )
        return

    if not out_path:
        print( dataframe.to_string() )
        return

    if not out_format:
        ## None or empty format
        out_format = get_format_from_path( out_path )

    switcher = {
        "xls":     lambda: dataframe.to_excel( out_path, index=False ),
        "csv":     lambda: dataframe.to_csv( out_path, encoding='utf-8', index=False ),
        "pickle":  lambda: store_object_simple( dataframe, out_path ),
    }
    store_func = switcher.get( out_format, None )

    if store_func is None:
        _LOGGER.error( "unsupported output format: %s", out_format )
        return

    store_func()


def get_format_from_path( file_path ):
    if "csv" in file_path:
        return "xls"
    if "xls" in file_path:
        return "xls"
    if "xlsx" in file_path:
        return "xls"
    if "pickle" in file_path:
        return "pickle"
    ## unknown extension -- use csv
    return "csv"


## ===================================================================
## ===================================================================


def main():
    parser = argparse.ArgumentParser(description='stock data grabber')
    parser.add_argument( '-la', '--logall', action='store_true', help='Log all messages' )

    subparsers = parser.add_subparsers( help='data providers', description="select one of subcommands", dest='subcommand', required=True )

    ## =================================================

    subparser = subparsers.add_parser('config_mode', help='Store data based on configuration file')
    subparser.set_defaults( func = lambda args: grab_by_config( parser, args ) )
    subparser.add_argument( '-cp', '--config_path', action='store', required=True, default="", help="Path for config file." )

    ## =================================================

    subparser = subparsers.add_parser('all_current', help='Store data from almost all providers using current data if required')
    subparser.set_defaults( func=grab_all )
    subparser.add_argument( '-of', '--out_format', action='store', required=True, default="", help="Output format, one of: csv, xls, pickle. If none given, then will be deduced based on extension of output path." )
    subparser.add_argument( '-od', '--out_dir', action='store', default="", help="Output directory" )

    ## =================================================

    subparser = subparsers.add_parser('gpw_curr_stock', help='GPW current stock')
    subparser.set_defaults( func=grab_simple_template( GpwCurrentStockData ) )
    subparser.add_argument( '-of', '--out_format', action='store', default="", help="Output format, one of: csv, xls, pickle. If none given, then will be deduced based on extension of output path." )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output file path" )

    subparser = subparsers.add_parser('gpw_curr_indexes', help='GPW current indexes (main, macro and sectors)')
    subparser.set_defaults( func=grab_simple_template( GpwCurrentIndexesData ) )
    subparser.add_argument( '-of', '--out_format', action='store', default="", help="Output format, one of: csv, xls, pickle. If none given, then will be deduced based on extension of output path." )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output file path" )

    ## =================================================

    subparser = subparsers.add_parser('gpw_isin_data', help='GPW ISIN data')
    subparser.set_defaults( func=grab_simple_template( GpwIsinMapData ) )
    subparser.add_argument( '-of', '--out_format', action='store', default="", help="Output format, one of: csv, xls, pickle. If none given, then will be deduced based on extension of output path." )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output file path" )

    subparser = subparsers.add_parser('gpw_stock_indicators', help='GPW stock indicators')
    subparser.set_defaults( func=grab_simple_template( GpwIndicatorsData ) )
    subparser.add_argument( '-of', '--out_format', action='store', default="", help="Output format, one of: csv, xls, pickle. If none given, then will be deduced based on extension of output path." )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output file path" )

    subparser = subparsers.add_parser('gpw_espi', help='GPW ESPI')
    subparser.set_defaults( func=grab_simple_template( GpwESPIData ) )
    subparser.add_argument( '-of', '--out_format', action='store', default="", help="Output format, one of: csv, xls, pickle. If none given, then will be deduced based on extension of output path." )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output file path" )

    ## =================================================

    subparser = subparsers.add_parser('gpw_curr_stock_intra', help='GPW current intraday stock data')
    subparser.set_defaults( func=grab_isin_template( GpwCurrentStockIntradayData ) )
    subparser.add_argument( '--isin', action='store', required=True, default="", help="ISIN" )
    subparser.add_argument( '-of', '--out_format', action='store', default="", help="Output format, one of: csv, xls, pickle. If none given, then will be deduced based on extension of output path." )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output file path" )

    subparser = subparsers.add_parser('gpw_curr_index_intra', help='GPW current intraday index data')
    subparser.set_defaults( func=grab_isin_template( GpwCurrentIndexIntradayData ) )
    subparser.add_argument( '--isin', action='store', required=True, default="", help="ISIN" )
    subparser.add_argument( '-of', '--out_format', action='store', default="", help="Output format, one of: csv, xls, pickle. If none given, then will be deduced based on extension of output path." )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output file path" )

    ## =================================================

    subparser = subparsers.add_parser('gpw_archive_data', help='GPW archive data')
    subparser.set_defaults( func=grab_date_template( GpwArchiveData ) )
    subparser.add_argument( '-d', '--date', action='store', required=True, default="", help="Archive date" )
    subparser.add_argument( '-of', '--out_format', action='store', default="", help="Output format, one of: csv, xls, pickle. If none given, then will be deduced based on extension of output path." )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output file path" )

    ## =================================================

    subparser = subparsers.add_parser('div_cal', help='Dividends calendar')
    subparser.set_defaults( func=grab_simple_template( DividendsCalendarData ) )
    subparser.add_argument( '-of', '--out_format', action='store', default="", help="Output format, one of: csv, xls, pickle. If none given, then will be deduced based on extension of output path." )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output file path" )

    ## =================================================

    subparser = subparsers.add_parser('fin_reps_cal', help='Financial reports calendar')
    subparser.set_defaults( func=grab_simple_template( FinRepsCalendarData ) )
    subparser.add_argument( '-of', '--out_format', action='store', default="", help="Output format, one of: csv, xls, pickle. If none given, then will be deduced based on extension of output path." )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output file path" )

    subparser = subparsers.add_parser('pub_fin_reps_cal', help='Published financial reports calendar')
    subparser.set_defaults( func=grab_simple_template( PublishedFinRepsCalendarData ) )
    subparser.add_argument( '-of', '--out_format', action='store', default="", help="Output format, one of: csv, xls, pickle. If none given, then will be deduced based on extension of output path." )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output file path" )

    ## =================================================

    subparser = subparsers.add_parser('global_indexes', help='Global indexes')
    subparser.set_defaults( func=grab_simple_template( GlobalIndexesData ) )
    subparser.add_argument( '-of', '--out_format', action='store', default="", help="Output format, one of: csv, xls, pickle. If none given, then will be deduced based on extension of output path." )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output file path" )

    ## =================================================

    subparser = subparsers.add_parser('metastock_intraday', help='MetaStock intraday data')
    subparser.set_defaults( func=grab_date_template( MetaStockIntradayData ) )
    subparser.add_argument( '-d', '--date', action='store', required=True, default="", help="Archive date" )
    subparser.add_argument( '-of', '--out_format', action='store', default="", help="Output format, one of: csv, xls, pickle. If none given, then will be deduced based on extension of output path." )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output file path" )

    ## =================================================

    subparser = subparsers.add_parser('curr_short_sell', help='Current short sellings')
    subparser.set_defaults( func=grab_simple_template( CurrentShortSellingsData ) )
    subparser.add_argument( '-of', '--out_format', action='store', default="", help="Output format, one of: csv, xls, pickle. If none given, then will be deduced based on extension of output path." )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output file path" )

    subparser = subparsers.add_parser('hist_short_sell', help='History short sellings')
    subparser.set_defaults( func=grab_simple_template( HistoryShortSellingsData ) )
    subparser.add_argument( '-of', '--out_format', action='store', default="", help="Output format, one of: csv, xls, pickle. If none given, then will be deduced based on extension of output path." )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output file path" )

    ## =================================================

    args = parser.parse_args()

#     if args.subcommand is None:
#         parser.print_usage()
#         print( "subcommand required" )
#         return

    logging.basicConfig()
    if args.logall is True:
        logging.getLogger().setLevel( logging.DEBUG )
    else:
        logging.getLogger().setLevel( logging.INFO )

    if "func" not in args:
        ## no command given
        return

    _LOGGER.info( "starting grab script" )

    succeed = args.func( args )

    if succeed:
        _LOGGER.info( "grabbing done" )
    else:
        _LOGGER.info( "unable to grab data" )


if __name__ == '__main__':
    main()
