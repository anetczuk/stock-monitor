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
from datetime import datetime

from typing import Dict, List, Tuple

from stockdataaccess import persist

from stockmonitor.datatypes.wallettypes import TransHistory, Transaction, TransactionMatchMode


_LOGGER = logging.getLogger(__name__)


StockId = Tuple[str, str]


class WalletData( persist.Versionable ):

    ## 0 - first version
    ## 1 - dict instead of list
    ## 2 - sort transactions
    ## 3 - add 'commission' field to transaction
    ## 4 - rename "stockList" to "_stockDict" and change key from ticker to pair (name, ticker)
    _class_version = 4

    def __init__(self):
        # key:   (stockName, ticker)
        # value: TransHistory
        self._stockDict: Dict[ StockId, TransHistory ] = {}

    def _convertstate_(self, dict_, dictVersion_ ):
        _LOGGER.info( "converting object from version %s to %s", dictVersion_, self._class_version )

        if dictVersion_ is None:
            dictVersion_ = 0

        dictVersion_ = max(dictVersion_, 0)

        if dictVersion_ == 0:
            dict_["stockList"] = {}
            dictVersion_ = 1

        if dictVersion_ == 1:
            histDict = dict_["stockList"]
            for _, transHist in histDict.items():
                transHist.sort()
            dictVersion_ = 2

        if dictVersion_ == 2:
            ## add commission field
            histDict = dict_["stockList"]
            for _, transHist in histDict.items():
                transSize = len(transHist.transactions)
                convertedList = []
                for i in range( 0, transSize ):
                    trans = transHist.transactions[i]
                    convertedList.append( Transaction( trans[0], trans[1], 0.0, trans[2] ) )
                transHist.transactions = convertedList
            dictVersion_ = 3

        if dictVersion_ == 3:
            # rename "stockList" to "_stockDict" and change key from ticker to pair (name, ticker)
            histDict = dict_["stockList"]
            newData = {}
            for ticker, transHist in histDict.items():
                stock_id = (ticker, ticker)
                newData[ stock_id ] = transHist
            dict_["_stockDict"] = histDict
            dictVersion_ = 4

        # pylint: disable=W0201
        self.__dict__ = dict_

    def __getitem__(self, ticker) -> TransHistory:
        for stock_id, hist in self._stockDict.items():
            stock_ticker = stock_id[1]
            if stock_ticker == ticker:
                return hist
        #return self._stockDict.get( ticker, None )

    def size(self):
        return len( self._stockDict )

    def clear(self):
        self._stockDict.clear()

    ## return all tickers (even sold)
    def tickers(self):
        tickers_set = set()
        for stock_id in self._stockDict:
            stock_ticker = stock_id[1]
            tickers_set.add( stock_ticker )
        return tickers_set

    def transactions(self, ticker) -> TransHistory:
        return self[ ticker ]

    ## returns List[ (ticker, curr amount, avg unit price) ]
    def currentItems( self, mode: TransactionMatchMode ) -> List[ Tuple[str, int, float] ]:
        ret: List[ Tuple[str, int, float] ] = []
        for stock_id, hist in self._stockDict.items():
            key = stock_id[1]
            if key is None:
                _LOGGER.warning("found wallet None key")
                continue
            val = hist.currentTransactionsAvg( mode )     # pair: (amount, unit_price)
            if val is not None:
                ret.append( (key, val[0], val[1]) )
        return ret

    # for backward compatibility
    def addTransactionData( self, ticker, amount, unitPrice, transTime: datetime = datetime.today(),
                            joinSimilar=True, commission=0.0 ):
        self.addTransaction( ticker, ticker, amount, unitPrice, transTime, joinSimilar, commission )

    def addTransaction( self, stockName, ticker, amount, unitPrice, transTime: datetime = datetime.today(),
             joinSimilar=True, commission=0.0 ):
        stock_id = ( stockName, ticker )
        transactions: TransHistory = self._stockDict.get( stock_id, None )
        if transactions is None:
            transactions = TransHistory()
            self._stockDict[ stock_id ] = transactions
        _LOGGER.debug( "adding transaction: %s %s %s %s %s", stock_id, amount, unitPrice, commission, transTime )
        transactions.add( amount, unitPrice, commission, transTime, joinSimilar )

    def addTransactionObject( self, stockId: StockId, transaction: Transaction, joinSimilar=True ):
        self.addTransaction( stockId[0], stockId[1], transaction.amount, transaction.unitPrice,
                             transaction.transTime, joinSimilar, commission=transaction.commission )

    def addWallet(self, wallet: 'WalletData', joinSimilar=True):
        for stockId, hist in wallet._stockDict.items():
            for trans in hist.transactions:
                self.addTransactionObject(stockId, trans, joinSimilar)

    ## get current tickers
    def getCurrentStock(self) -> List[ str ]:
        ret = []
        for stockId, hist in self._stockDict.items():
            amount = hist.currentAmount()
            if amount > 0:
                ticker = stockId[1] if stockId else None
                ret.append( ticker )
        return ret
