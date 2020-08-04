#!/usr/bin/python3
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

import sys
import os

import argparse
import logging
import datetime

import stockmonitor.logger as logger

from stockmonitor.dataaccess.datatype import ArchiveDataType
from stockmonitor.dataaccess.stockdata import StockAnalysis

# from stockmonitor.gui.main_window import MainWindow
#
# from stockmonitor.gui.qt import QApplication
# from stockmonitor.gui.sigint import setup_interrupt_handling


logger.configure()
_LOGGER = logging.getLogger(__name__)

script_dir = os.path.dirname(os.path.realpath(__file__))

tmp_dir = script_dir + "/../../tmp/"


def crisisResults( analysis ):
    maxFromDay = datetime.date( 2020, 2, 1 )
    maxToDay   = datetime.date( 2020, 3, 5 )
    analysis.loadMax( ArchiveDataType.MAX, maxFromDay, maxToDay)

    minFromDay = datetime.date( 2020, 3, 6 )
    minToDay   = datetime.date( 2020, 3, 22 )
    analysis.loadMin( ArchiveDataType.MIN, minFromDay, minToDay)

#     analysis.loadCurr( ArchiveDataType.CLOSING, offset=-1 )
    analysis.loadCurr( ArchiveDataType.CLOSING, offset=-1 )

    analysis.calcBestValue( 0.6, tmp_dir + "out/crisis_stock_value.csv" )
    analysis.calcBestRaise( 0.1, tmp_dir + "out/crisis_stock_raise.csv" )


def crisisResults2( analysis ):
    recentDay = analysis.getRecentValidDay()
    fromDay = datetime.date( 2020, 2, 1 )
    toDay   = recentDay
    analysis.loadMax( ArchiveDataType.MAX, fromDay, toDay)

    minFromDay = datetime.date( 2020, 3, 6 )
    minToDay   = datetime.date( 2020, 3, 22 )
    analysis.loadMin( ArchiveDataType.MIN, fromDay, toDay)

#     analysis.loadCurr( ArchiveDataType.CLOSING, offset=-1 )
    analysis.loadCurr( ArchiveDataType.CLOSING, day=recentDay )

    analysis.calcBestValue( 999990.6, tmp_dir + "out/crisis_full_stock_value.csv" )
    analysis.calcBestRaise( 999990.1, tmp_dir + "out/crisis_full_stock_raise.csv" )


def weekStockResults( analysis, periodLength=8 ):
    recentDay = analysis.getRecentValidDay()
    startDay = recentDay - datetime.timedelta(days=periodLength)
#     endDay = recentDay - datetime.timedelta(days=1)

    analysis.loadMax( ArchiveDataType.MAX, startDay, recentDay)
    analysis.loadMin( ArchiveDataType.MIN, startDay, recentDay)
    analysis.loadCurr( ArchiveDataType.CLOSING, day=recentDay )

    analysis.calcBestValue( 999990.8, tmp_dir + "out/week_stock_value.csv" )
    analysis.calcBestRaise( 999990.2, tmp_dir + "out/week_stock_raise.csv" )


def weekVolumeResults( analysis ):
    recentDay = analysis.getRecentValidDay()
    startDay = recentDay - datetime.timedelta(days=8)
#     endDay = recentDay - datetime.timedelta(days=1)

    analysis.loadMax( ArchiveDataType.VOLUME, startDay, recentDay)

    analysis.loadCurr( ArchiveDataType.VOLUME, day=recentDay )

    analysis.calcBiggestRaise( 0.01, tmp_dir + "out/week_stock_volume.csv" )


def dayResults( analysis ):
    analysis.loadCurr( ArchiveDataType.VOLUME, offset=-1 )
    analysis.calcGreater( 100000, tmp_dir + "out/day_stock_volume.csv" )

    analysis.loadCurr( ArchiveDataType.TRADING, offset=-1 )
    analysis.calcGreater( 30000, tmp_dir + "out/day_stock_trading.csv" )

def tradingResults( analysis ):
    recentDay = analysis.getRecentValidDay( checkGiven=True )
    startDay = recentDay - datetime.timedelta(days=6)
    analysis.loadSum( ArchiveDataType.TRADING, startDay, recentDay)
    analysis.calcGreatestSum( tmp_dir + "out/week_stock_trading.csv" )

def variance( analysis ):
    recentDay = analysis.getRecentValidDay( checkGiven=True )
    startDay = recentDay - datetime.timedelta(days=6)
    analysis.calcVariance( startDay, recentDay, tmp_dir + "out/stock_variance.csv" )


def run_app(args):

    analysis = StockAnalysis()

    crisisResults( analysis )
    crisisResults2( analysis )

    weekStockResults( analysis, 5 )

    weekVolumeResults( analysis )
    dayResults( analysis )

#     analysis.calcWeekend(4)
#
#     analysis.calcMonday(4)
#     analysis.calcFriday(4)		#TODO: fix, downloads future file

    tradingResults( analysis )

    variance( analysis )

    return 0

#     ## GUI
#     app = QApplication(sys.argv)
#     app.setApplicationName("StockMonitor")
#     app.setOrganizationName("arnet")
#     ### app.setOrganizationDomain("www.my-org.com")
#
#     window = MainWindow()
#     window.loadSettings()
#
#     window.show()
#
#     setup_interrupt_handling()
#
#     exitCode = app.exec_()
#
#     if exitCode == 0:
#         window.saveSettings()
#
#     return exitCode


def create_parser( parser: argparse.ArgumentParser = None ):
    if parser is None:
        parser = argparse.ArgumentParser(description='Stock Monitor')
    parser.add_argument('--minimized', action='store_const', const=True, default=False, help='Start minimized' )
    return parser


def main( args=None ):
    if args is None:
        parser = create_parser()
        args = parser.parse_args()

    _LOGGER.debug("Starting the application")
    _LOGGER.debug("Logger log file: %s" % logger.log_file)

    exitCode = 1

    try:
        exitCode = run_app(args)

    except BaseException:
        _LOGGER.exception("Exception occurred")
        raise

    finally:
        sys.exit(exitCode)

    return exitCode


if __name__ == '__main__':
    main()
