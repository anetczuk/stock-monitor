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

import logging
import argparse
import datetime

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
        provider: BaseWorksheetData = GRABBER_CLASS()

        dataframe: DataFrame = provider.accessWorksheetData()
        if dataframe is None:
            _LOGGER.error( "unable to grab data" )
            return

        if not args.out_path:
            print( dataframe.to_string() )
            return

        if "xlsx" in args.out_path:
            dataframe.to_excel( args.out_path, index=False )
        else:
            dataframe.to_csv( args.out_path, encoding='utf-8', index=False )

    return grab_data


def grab_isin_template( GRABBER_CLASS ):

    def grab_data( args ):
        provider: BaseWorksheetData = GRABBER_CLASS( args.isin )

        dataframe: DataFrame = provider.accessWorksheetData()
        if dataframe is None:
            _LOGGER.error( "unable to grab data" )
            return

        if not args.out_path:
            print( dataframe.to_string() )
            return

        if "xlsx" in args.out_path:
            dataframe.to_excel( args.out_path, index=False )
        else:
            dataframe.to_csv( args.out_path, encoding='utf-8', index=False )

    return grab_data


def grab_date_template( GRABBER_CLASS ):

    def grab_data( args ):
        input_date = datetime.datetime.strptime( args.date, "%Y-%m-%d").date()

        provider: BaseWorksheetData = GRABBER_CLASS( input_date )

        dataframe: DataFrame = provider.accessWorksheetData()
        if dataframe is None:
            _LOGGER.error( "unable to grab data" )
            return

        if not args.out_path:
            print( dataframe.to_string() )
            return

        if "xlsx" in args.out_path:
            dataframe.to_excel( args.out_path, index=False )
        else:
            dataframe.to_csv( args.out_path, encoding='utf-8', index=False )

    return grab_data


## ===================================================================


## ===================================================================
## ===================================================================


def main():
    parser = argparse.ArgumentParser(description='stock data grabber')
    parser.add_argument( '-la', '--logall', action='store_true', help='Log all messages' )

    subparsers = parser.add_subparsers( help='data providers' )

    ## =================================================

    subparser = subparsers.add_parser('gpw_curr_stock', help='GPW current stock')
    subparser.set_defaults( func=grab_simple_template( GpwCurrentStockData ) )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )

    subparser = subparsers.add_parser('gpw_curr_indexes', help='GPW current indexes')
    subparser.set_defaults( func=grab_simple_template( GpwCurrentIndexesData ) )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )

#     subparser = subparsers.add_parser('gpw_main_indexes', help='GPW main indexes')
#     subparser.set_defaults( func=grab_simple_template( GpwMainIndexesData ) )
#     subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )
#
#     subparser = subparsers.add_parser('gpw_macro_indexes', help='GPW macro indexes')
#     subparser.set_defaults( func=grab_simple_template( GpwMacroIndexesData ) )
#     subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )
#
#     subparser = subparsers.add_parser('gpw_sectors_indexes', help='GPW sectors indexes')
#     subparser.set_defaults( func=grab_simple_template( GpwSectorsIndexesData ) )
#     subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )

    ## =================================================

    subparser = subparsers.add_parser('gpw_isin_data', help='GPW ISIN data')
    subparser.set_defaults( func=grab_simple_template( GpwIsinMapData ) )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )

    subparser = subparsers.add_parser('gpw_stock_indicators', help='GPW stock indicators')
    subparser.set_defaults( func=grab_simple_template( GpwIndicatorsData ) )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )

    subparser = subparsers.add_parser('gpw_espi', help='GPW ESPI')
    subparser.set_defaults( func=grab_simple_template( GpwESPIData ) )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )

    ## =================================================

    subparser = subparsers.add_parser('gpw_curr_stock_intra', help='GPW current intraday stock data')
    subparser.set_defaults( func=grab_isin_template( GpwCurrentStockIntradayData ) )
    subparser.add_argument( '--isin', action='store', required=True, default="", help="ISIN" )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )

    subparser = subparsers.add_parser('gpw_curr_index_intra', help='GPW current intraday index data')
    subparser.set_defaults( func=grab_isin_template( GpwCurrentIndexIntradayData ) )
    subparser.add_argument( '--isin', action='store', required=True, default="", help="ISIN" )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )

    ## =================================================

    subparser = subparsers.add_parser('gpw_archive_data', help='GPW archive data')
    subparser.set_defaults( func=grab_date_template( GpwArchiveData ) )
    subparser.add_argument( '-d', '--date', action='store', required=True, default="", help="Archive date" )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )

    ## =================================================

    subparser = subparsers.add_parser('div_cal', help='Dividends calendar')
    subparser.set_defaults( func=grab_simple_template( DividendsCalendarData ) )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )

    ## =================================================

    subparser = subparsers.add_parser('fin_reps_cal', help='Financial reports calendar')
    subparser.set_defaults( func=grab_simple_template( FinRepsCalendarData ) )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )

    subparser = subparsers.add_parser('pub_fin_reps_cal', help='Published financial reports calendar')
    subparser.set_defaults( func=grab_simple_template( PublishedFinRepsCalendarData ) )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )

    ## =================================================

    subparser = subparsers.add_parser('global_indexes', help='Global indexes')
    subparser.set_defaults( func=grab_simple_template( GlobalIndexesData ) )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )

    ## =================================================

    subparser = subparsers.add_parser('metastock_intraday', help='MetaStock intraday data')
    subparser.set_defaults( func=grab_date_template( MetaStockIntradayData ) )
    subparser.add_argument( '-d', '--date', action='store', required=True, default="", help="Archive date" )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )

    ## =================================================

    subparser = subparsers.add_parser('curr_short_sell', help='Current short sellings')
    subparser.set_defaults( func=grab_simple_template( CurrentShortSellingsData ) )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )

    subparser = subparsers.add_parser('hist_short_sell', help='History short sellings')
    subparser.set_defaults( func=grab_simple_template( HistoryShortSellingsData ) )
    subparser.add_argument( '-op', '--out_path', action='store', default="", help="Output CSV/XLSX file path" )

    ## =================================================

    args = parser.parse_args()

    logging.basicConfig()
    if args.logall is True:
        logging.getLogger().setLevel( logging.DEBUG )
    else:
        logging.getLogger().setLevel( logging.INFO )

    if "func" not in args:
        ## no command given
        return

    _LOGGER.debug( "starting grab script" )

    args.func( args )

    _LOGGER.debug( "grabbing done" )


if __name__ == '__main__':
    main()
