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

import unittest

import datetime
import codecs
from pandas.core.frame import DataFrame

from stockdataaccess.dataaccess.worksheetdata import WorksheetStorageMock

from stockmonitor.datatypes.wallettypes import WalletData, TransHistory
from stockmonitor.dataaccess.transactionsloader import parse_mb_transactions_file
from stockmonitor.gui.dataobject import DataObject

from teststockdataaccess import data
from teststockmonitor import data as localdata


class DataObjectTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_addFavGroup(self):
        dataobject = DataObject()
        self.assertEqual( dataobject.undoStack.count(), 0 )
        dataobject.addFavGroup("xxx")
        self.assertEqual( dataobject.undoStack.count(), 1 )
        dataobject.addFavGroup("xxx")
        self.assertEqual( dataobject.undoStack.count(), 1 )

    def test_renameFavGrp(self):
        dataobject = DataObject()
        dataobject.addFavGroup("xxx")
        self.assertEqual( len(dataobject.favs.favsList), 1 )

        dataobject.renameFavGroup("xxx", "yyy")
        self.assertEqual( len(dataobject.favs.favsList), 1 )

        xxxFavs = dataobject.favs.getFavs( "xxx" )
        self.assertEqual( xxxFavs, None )

        yyyFavs = dataobject.favs.getFavs( "yyy" )
        self.assertNotEqual( yyyFavs, None )

    def test_deleteFavGrp(self):
        dataobject = DataObject()
        dataobject.addFavGroup("xxx")
        self.assertEqual( len(dataobject.favs.favsList), 1 )

        dataobject.deleteFavGroup("xxx")
        self.assertEqual( len(dataobject.favs.favsList), 0 )

    def test_deleteFavGrp_duplicates(self):
        dataobject = DataObject()
        dataobject.addFavGroup("xxx")
        dataobject.addFavGroup("xxx")
        self.assertEqual( len(dataobject.favs.favsList), 1 )

        dataobject.deleteFavGroup("xxx")
        self.assertEqual( len(dataobject.favs.favsList), 0 )

    def test_addFav_duplicates(self):
        dataobject = DataObject()
        dataobject.addFavGroup("xxx")
        self.assertEqual( len(dataobject.favs.favsList), 1 )

        dataobject.addFav("xxx", "aaa")
        self.assertEqual( dataobject.undoStack.count(), 2 )

        dataobject.addFav("xxx", "aaa")
        self.assertEqual( dataobject.undoStack.count(), 2 )

    def test_addFav_duplicates_list(self):
        dataobject = DataObject()
        dataobject.addFav( "xxx", "aaa" )
        self.assertEqual( dataobject.undoStack.count(), 1 )

        dataobject.addFav( "xxx", ["aaa", "bbb"] )
        self.assertEqual( dataobject.undoStack.count(), 2 )

    def test_getWalletStock(self):
        dataobject = DataObject()
        dataPath = data.get_data_path( "recent_data_TKO.xls" )
        dataobject.gpwCurrentSource.stockData.dao.storage = WorksheetStorageMock()
        dataobject.gpwCurrentSource.stockData.dao.parseWorksheetFromFile( dataPath )
        dataobject.wallet.add( "CDR", 1, 300.0 )
        stock = dataobject.getWalletStock()
        self.assertEqual( stock is not None, True )

    def test_getWalletState_oldest(self):
        dataobject = DataObject()
        dataobject.matchTransactionsOldest()

        dataPath = data.get_data_path( "akcje_2021-12-21_20-00.xls" )
        dataobject.gpwCurrentSource.stockData.dao.storage = WorksheetStorageMock()
        dataobject.gpwCurrentSource.stockData.dao.parseWorksheetFromFile( dataPath )

        ## CDP curr price: 360.0 (from recent_data_TKO.xls)
        dataobject.wallet.add( "CDR", -1, 300.0, datetime.datetime(2020, 10, 6, 15, 41, 33), commission=0.1 )
        dataobject.wallet.add( "CDR",  1, 200.0, datetime.datetime(2020, 10, 5, 15, 41, 33), commission=0.1 )
        dataobject.wallet.add( "CDR",  1, 260.0, datetime.datetime(2020, 10, 4, 15, 41, 33), commission=0.1 )

        walletVal, walletProfit, change, gain, overallProfit = dataobject.getWalletState()
        self.assertEqual( walletVal, 186.36 )
        self.assertEqual( walletProfit, -13.74 )
        self.assertEqual( change, '-3.46%' )
        self.assertEqual( gain, 39.8 )
        self.assertEqual( overallProfit, 26.06 )

    def test_getWalletState_best(self):
        dataobject = DataObject()
        dataobject.matchTransactionsBest()

        dataPath = data.get_data_path( "akcje_2021-12-21_20-00.xls" )
        dataobject.gpwCurrentSource.stockData.dao.storage = WorksheetStorageMock()
        dataobject.gpwCurrentSource.stockData.dao.parseWorksheetFromFile( dataPath )

        ## CDP curr price: 360.0 (from recent_data_TKO.xls)
        dataobject.wallet.add( "CDR", -1, 300.0, datetime.datetime(2020, 10, 6, 15, 41, 33), commission=0.1 )
        dataobject.wallet.add( "CDR",  1, 260.0, datetime.datetime(2020, 10, 5, 15, 41, 33), commission=0.1 )
        dataobject.wallet.add( "CDR",  1, 200.0, datetime.datetime(2020, 10, 4, 15, 41, 33), commission=0.1 )

        walletVal, walletProfit, change, gain, overallProfit = dataobject.getWalletState()
        self.assertEqual( walletVal, 186.36 )
        self.assertEqual( walletProfit, -73.74 )
        self.assertEqual( change, '-3.46%' )
        self.assertEqual( gain, 99.8 )
        self.assertEqual( overallProfit, 26.06 )

    def test_getWalletState_recent(self):
        dataobject = DataObject()
        dataobject.matchTransactionsRecent()

        dataPath = data.get_data_path( "akcje_2021-12-21_20-00.xls" )
        dataobject.gpwCurrentSource.stockData.dao.storage = WorksheetStorageMock()
        dataobject.gpwCurrentSource.stockData.dao.parseWorksheetFromFile( dataPath )

        ## CDP curr price: 360.0 (from recent_data_TKO.xls)
        dataobject.wallet.add( "CDR", -1, 300.0, datetime.datetime(2020, 10, 6, 15, 41, 33), commission=0.1 )
        dataobject.wallet.add( "CDR",  1, 260.0, datetime.datetime(2020, 10, 5, 15, 41, 33), commission=0.1 )
        dataobject.wallet.add( "CDR",  1, 200.0, datetime.datetime(2020, 10, 4, 15, 41, 33), commission=0.1 )

        walletVal, walletProfit, change, gain, overallProfit = dataobject.getWalletState()
        self.assertEqual( walletVal, 186.36 )
        self.assertEqual( walletProfit, -13.74 )
        self.assertEqual( change, '-3.46%' )
        self.assertEqual( gain, 39.8 )
        self.assertEqual( overallProfit, 26.06 )

    def test_importWalletTransactions(self):
        importedData = DataFrame( {'trans_time': ['28.10.2020 09:10:07'],
                                   'name': ["CCC"],
                                   'k_s': ['S'],
                                   'amount': [10],
                                   'unit_price': ['10.2'] } )
        dataObject = DataObject()
        wallet: WalletData = dataObject.wallet
        self.assertEqual( wallet.size(), 0 )

        dataObject.importWalletTransactions( importedData, True )
        self.assertEqual( wallet.size(), 1 )

        trans: TransHistory = wallet["CCC"]
        self.assertEqual( len( trans ), 1 )
        self.assertEqual( trans[0].amount, -10 )

        dataObject.importWalletTransactions( importedData, True )

        self.assertEqual( wallet.size(), 1 )
        self.assertEqual( len( trans ), 1 )
        self.assertEqual( trans[0].amount, -10 )

    def test_importWalletTransactions_sametime(self):
        transactionsPath = localdata.get_data_path( "transactions_bad_separator.csv" )

        with codecs.open(transactionsPath, 'r', encoding='utf-8', errors='replace') as srcFile:
            importedData = parse_mb_transactions_file( srcFile )

        dataObject = DataObject()
        dataObject.importWalletTransactions( importedData )

        wallet: WalletData = dataObject.wallet
        self.assertEqual( wallet.size(), 1 )

        trans: TransHistory = wallet["ENT"]
        amount = trans.currentAmount()
        self.assertEqual( amount, 0 )
