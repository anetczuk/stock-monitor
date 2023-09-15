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
from typing import Dict, List, Tuple

import datetime
#from datetime import datetime, date, timedelta
import functools

from pandas.core.frame import DataFrame

from stockdataaccess import persist
from stockdataaccess.dataaccess.datatype import StockDataType
from stockdataaccess.dataaccess.gpw.gpwdata import GpwIndicatorsData
from stockdataaccess.dataaccess.gpw.gpwcurrentdata import GpwCurrentStockData, GpwCurrentIndexesData
from stockdataaccess.dataaccess.gpw.gpwespidata import GpwESPIData

from stockdataaccess.dataaccess.dividendsdata import DividendsCalendarData
from stockdataaccess.dataaccess.finreportscalendardata import PublishedFinRepsCalendarData, FinRepsCalendarData
from stockdataaccess.dataaccess.globalindexesdata import GlobalIndexesData
from stockdataaccess.dataaccess.shortsellingsdata import CurrentShortSellingsData, HistoryShortSellingsData

from stockmonitor.datatypes.datatypes import UserContainer,\
    FavData, WalletData, MarkersContainer, MarkerEntry
from stockmonitor.datatypes.stocktypes import BaseWorksheetDAOProvider, GpwStockIntradayMap,\
    GpwIndexIntradayMap, StockDataProvider, StockDataWrapper
from stockmonitor.datatypes.wallettypes import broker_commission, TransHistory,\
    Transaction


_LOGGER = logging.getLogger(__name__)


##
##
##
class DataContainer():

    def __init__(self):
        self.userContainer        = UserContainer()                   ## user data

        self.gpwCurrentSource     = StockDataWrapper( GpwCurrentStockData() )
        self.gpwStockIntradayData = GpwStockIntradayMap()
        self.gpwIndexIntradayData = GpwIndexIntradayMap()

        self.gpwESPIData        = GpwESPIData()

        self.gpwIndexesData     = GpwCurrentIndexesData()
        self.globalIndexesData  = GlobalIndexesData()
        self.gpwIndicatorsData  = GpwIndicatorsData()
        self.gpwDividendsData   = DividendsCalendarData()

        self.gpwReportsData     = FinRepsCalendarData()
        self.gpwPubReportsData  = PublishedFinRepsCalendarData()

        self.gpwCurrentShortSellingsData = CurrentShortSellingsData()
        self.gpwHistoryShortSellingsData = HistoryShortSellingsData()

#         self.gpwIsinMap         = GpwIsinMapData()

    def store( self, outputDir ):
        outputFile = outputDir + "/gpwcurrentheaders.obj"
        persist.store_object( self.gpwCurrentHeaders, outputFile )
        return self.userContainer.store( outputDir )

    def load( self, inputDir ):
        self.userContainer.load( inputDir )
        inputFile = inputDir + "/gpwcurrentheaders.obj"
        headers = persist.load_object_simple( inputFile, {} )
        self.gpwCurrentSource.stockHeaders = headers
        #self.gpwCurrentHeaders = headers
        self.updateWalletFavGroup()
        self.updateMarkersFavGroup()
        self.updateAllFavsGroup()

    ## ======================================================================

    @property
    def wallet(self) -> WalletData:
        return self.userContainer.wallet

    @property
    def favs(self) -> FavData:
        return self.userContainer.favs

    @favs.setter
    def favs(self, newData: FavData):
        self.userContainer.favs = newData

    @property
    def markers(self) -> MarkersContainer:
        return self.userContainer.markers

    @markers.setter
    def markers(self, newData: FavData):
        self.userContainer.markers = newData

    @property
    def notes(self) -> Dict[str, str]:
        return self.userContainer.notes

    @notes.setter
    def notes(self, newData: Dict[str, str]):
        self.userContainer.notes = newData

    ## ======================================================================

    def getAllFavs(self):
        allFavsSet = set()
        for group, favs in self.favs.favsList.items():
            if group == "All":
                continue
            allFavsSet |= set( favs )
        return allFavsSet

    def getFavStock(self, favGroup):
        stockList = self.favs.getFavs( favGroup )
        return self.gpwCurrentData.getStockData( stockList )

    ## ======================================================================

    def getMarkersData(self):
        columnsList = [ "Nazwa", "Ticker", "Typ operacji", "Liczba", "Kurs operacji",
                        "Wartość operacji",
                        "Aktualny kurs", "Zm.do k.oper.[%]", "Różn. wartości [PLN]",
                        "Kolor", "Uwagi" ]
        rowsList = []
        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData
        mSize = self.markers.size()
        for i in range(0, mSize):
            entry: MarkerEntry = self.markers.get( i )

            operationVal = entry.amount * entry.value
            notes        = entry.notes
            if notes is None:
                notes = ""

            stockName    = currentStock.getNameFromTicker( entry.ticker )
            stockValue   = currentStock.getRecentValueByTicker( entry.ticker )

#             if stockValue is None:
#                 _LOGGER.info( "None type:", entry.ticker, stockName )

            if stockName is None or stockValue is None or stockValue == '-':
                rowDict = {}
                rowDict[ columnsList[ 0] ] = stockName
                rowDict[ columnsList[ 1] ] = entry.ticker
                rowDict[ columnsList[ 2] ] = entry.operationName()
                rowDict[ columnsList[ 3] ] = entry.amount
                rowDict[ columnsList[ 4] ] = entry.value
                rowDict[ columnsList[ 5] ] = operationVal
                rowDict[ columnsList[ 6] ] = "-"                        ## stock value
                rowDict[ columnsList[ 7] ] = "-"                        ## wymagana zmiana
                rowDict[ columnsList[ 8] ] = "-"                        ## zysk
                rowDict[ columnsList[ 9] ] = entry.color
                rowDict[ columnsList[10] ] = notes
                rowsList.append( rowDict )
                continue

            reqChangePnt = entry.requiredChange( stockValue )
            reqChangePnt = round( reqChangePnt, 2 )
            reqValue     = entry.requiredValue( stockValue )
            reqValue     = round( reqValue, 2 )

            rowDict = {}
            rowDict[ columnsList[ 0] ] = stockName
            rowDict[ columnsList[ 1] ] = entry.ticker
            rowDict[ columnsList[ 2] ] = entry.operationName()
            rowDict[ columnsList[ 3] ] = entry.amount
            rowDict[ columnsList[ 4] ] = entry.value
            rowDict[ columnsList[ 5] ] = operationVal
            rowDict[ columnsList[ 6] ] = stockValue                 ## stock value
            rowDict[ columnsList[ 7] ] = reqChangePnt               ## wymagana zmiana
            rowDict[ columnsList[ 8] ] = reqValue                   ## zysk
            rowDict[ columnsList[ 9] ] = entry.color
            rowDict[ columnsList[10] ] = notes
            rowsList.append( rowDict )

        dataFrame = DataFrame( rowsList )
        dataFrame = dataFrame.fillna("-")
        return dataFrame

    ## ======================================================================

    def transactionsMatchMode(self):
        return self.userContainer.transactionsMatchMode

    ## ======================================================================

    def clearWalletTransactions(self):
        self.userContainer.wallet = WalletData()
        self.updateWalletFavGroup()

    # return True if data changed, otherwise False
    def importWalletTransactions(self, dataFrame: DataFrame, addTransactions=False):
        if dataFrame is None:
            _LOGGER.warning( "None dataframe given" )
            return False

#         wallet: WalletData = self.wallet
        importWallet = WalletData()

        for _, row in dataFrame.iterrows():
            transTime   = row['trans_time']
            stockName   = row['name']
            oper        = row['k_s']
            amount      = row['amount']
            unit_price  = row['unit_price']
            commission  = row.get('commission_value', 0.0)

#             print("raw row:", transTime, stockName, oper, amount, unit_price)

            dateObject = None
            try:
                ## 31.03.2020 13:21:44
                dateObject = datetime.datetime.strptime(transTime, '%d.%m.%Y %H:%M:%S')
            except ValueError:
                dateObject = None

            ticker = self.gpwCurrentData.getTickerFromName( stockName )
            if ticker is None:
                _LOGGER.warning( "could not find stock ticker for name: >%s<", stockName )

            if oper == "K":
                importWallet.addTransaction( stockName, ticker,  amount, unit_price, dateObject, False, commission=commission )
            elif oper == "S":
                importWallet.addTransaction( stockName, ticker, -amount, unit_price, dateObject, False, commission=commission )

        if addTransactions:
            ## merge wallets
            self.wallet.addWallet( importWallet )
        else:
            ## replace wallet
            self.userContainer.wallet = importWallet

        self.updateWalletFavGroup()
        return True

    def updateAllFavsGroup(self):
        allFavsSet = self.getAllFavs()

        currFavsSet = self.favs.getFavs( "All" )
        if currFavsSet is None:
            currFavsSet = set()
        else:
            currFavsSet = set( currFavsSet )

        if allFavsSet != currFavsSet:
            _LOGGER.debug("updating All favs")
            self.favs.setFavs( "All", allFavsSet )
            return True
        return False

    def updateWalletFavGroup(self):
        wallet: WalletData = self.wallet
        walletSet = set( wallet.getCurrentStock() )

        currFavsSet = self.favs.getFavs( "Wallet" )
        if currFavsSet is None:
            currFavsSet = set()
        else:
            currFavsSet = set( currFavsSet )

        if walletSet != currFavsSet:
            _LOGGER.debug("updating Wallet favs")
            self.favs.setFavs( "Wallet", walletSet )
            return True
        return False

    def updateMarkersFavGroup(self):
        markers: MarkersContainer = self.markers
        markersSet = markers.getTickers()

        currFavsSet = self.favs.getFavs( "Markers" )
        if currFavsSet is None:
            currFavsSet = set()
        else:
            currFavsSet = set( currFavsSet )

        if markersSet != currFavsSet:
            _LOGGER.debug("updating Markers favs")
            self.favs.setFavs( "Markers", markersSet )
            return True
        return False

    ## ======================================================================

    # pylint: disable=R0914
    def getWalletStock(self, show_soldout=True) -> DataFrame:
        columnsList = [ "Nazwa", "Ticker", "Liczba", "Średni kurs nabycia",
                        "Kurs",
                        "Zm.do k.odn.[%]", "Zm.do k.odn.[PLN]",
                        "Wartość [PLN]", "Udział [%]",
                        "Zysk [%]", "Zysk [PLN]", "Zysk całkowity [PLN]" ]

        # apply_on_column( dataFrame, 'Zm.do k.odn.(%)', convert_float )

        walletState = self.getWalletState()
        walletValue = walletState[0]

        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData

        dataChangeIndex = currentStock.getDataColumnIndex( StockDataType.CHANGE_TO_REF )

        rowsList = []

        transMode = self.userContainer.transactionsMatchMode

        for stock_id, transactions in self.wallet._stockDict.items():
            stock_name: str = stock_id[0] if stock_id else None
            ticker: str     = stock_id[1] if stock_id else None

            amount, buy_unit_price = transactions.currentTransactionsAvg( transMode )
            if show_soldout is False and amount <= 1:
                continue
            
            currentStockRow = currentStock.getRowByTicker( ticker )

            if not ticker:
                ticker = ""

            if currentStockRow is None or currentStockRow.empty:
                _LOGGER.warning( "could not find stock by ticker: %s", ticker )
                rowDict = {}
                rowDict[ columnsList[ 0] ] = stock_name
                rowDict[ columnsList[ 1] ] = ticker
                rowDict[ columnsList[ 2] ] = amount                         ## liczba
                rowDict[ columnsList[ 3] ] = round( buy_unit_price, 4 )     ## sredni kurs nabycia
                rowDict[ columnsList[ 4] ] = "-"                            ## kurs
                rowDict[ columnsList[ 5] ] = "-"
                rowDict[ columnsList[ 6] ] = "-"
                rowDict[ columnsList[ 7] ] = "-"
                rowDict[ columnsList[ 8] ] = "-"
                rowDict[ columnsList[ 9] ] = "-"
                rowDict[ columnsList[10] ] = "-"
                rowDict[ columnsList[11] ] = "-"
                rowsList.append( rowDict )
                continue

            currUnitValue = GpwCurrentStockData.unitPrice( currentStockRow )

            currChangeRaw = currentStockRow.iloc[ dataChangeIndex ]
            currChangePnt = 0
            if currChangeRaw != "-":
                currChangePnt = float( currChangeRaw )

            sellValue  = currUnitValue * amount                 ## amount is positive
            sellValue -= broker_commission( sellValue )

            ## ( curr_unit_price - ref_unit_price ) * unit_price * amount
            valueChange = currChangePnt / 100.0 * sellValue

            participation = sellValue / walletValue * 100.0

            buyValue  = buy_unit_price * amount
            profit    = sellValue - buyValue
            profitPnt = 0
            if buyValue != 0:
                profitPnt = profit / buyValue * 100.0

            totalProfit = transactions.transactionsOverallProfit() + sellValue

            rowDict = {}
            rowDict[ columnsList[ 0] ] = stock_name
            rowDict[ columnsList[ 1] ] = ticker
            rowDict[ columnsList[ 2] ] = amount                         ## liczba
            rowDict[ columnsList[ 3] ] = round( buy_unit_price, 4 )     ## sredni kurs nabycia
            rowDict[ columnsList[ 4] ] = round( currUnitValue, 2 )      ## kurs
            rowDict[ columnsList[ 5] ] = round( currChangePnt, 2 )      ## zm. kur. odn %
            rowDict[ columnsList[ 6] ] = round( valueChange, 2 )        ## zm. kur. odn. PLN
            rowDict[ columnsList[ 7] ] = round( sellValue, 2 )          ## wartosc
            rowDict[ columnsList[ 8] ] = round( participation, 2 )      ## udzial
            rowDict[ columnsList[ 9] ] = round( profitPnt, 2 )          ## zysk %
            rowDict[ columnsList[10] ] = round( profit, 2 )             ## zysk PLN
            rowDict[ columnsList[11] ] = round( totalProfit, 2 )        ## zysk calk.
            rowsList.append( rowDict )


        def sort_wallet_profit(item_a, item_b):
            value_a = item_a[columnsList[9]]
            value_b = item_b[columnsList[9]]

            if isinstance(value_a, str):
                value_a = -float("inf")
            if isinstance(value_b, str):
                value_b = -float("inf")
            
            if value_a < value_b:
                return -1
            if value_a > value_b:
                return 1
            return 0

        rowsList.sort( key=functools.cmp_to_key(sort_wallet_profit), reverse = True )           # sort
        #rowsList.sort( key=lambda x: (not isinstance(x, str), x[columnsList[9]]) )           # sort

        dataFrame = DataFrame( rowsList )
        return dataFrame

    # pylint: disable=R0914
    def getWalletBuyTransactions(self, groupByDay=False) -> DataFrame:
        columnsList = [ "Nazwa", "Ticker", "Liczba", "Kurs kupna", "Opłata", "Wartość",
                        "Kurs aktualny",
                        "Zysk", "Zysk %", "Data transakcji" ]

        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData

        rowsList = []

        transMode = self.userContainer.transactionsMatchMode

        stock_id: Tuple[ str, str ]
        transactions: TransHistory
        for stock_id, transactions in self.wallet._stockDict.items():
            stock_name: str = stock_id[0] if stock_id else None
            ticker: str     = stock_id[1] if stock_id else None

            stock_unit_value = None
            currentStockRow = currentStock.getRowByTicker( ticker )
            if currentStockRow is None or currentStockRow.empty:
                _LOGGER.warning( "could not find stock by ticker: %s", ticker )
            else:
                stock_unit_value = GpwCurrentStockData.unitPrice( currentStockRow )

            currTransactions = transactions.currentTransactions( transMode )
            if groupByDay:
                currTransactions = TransHistory.groupTransactionsByDay( currTransactions )

            if not ticker:
                ticker = ""

            for item in currTransactions:
                trans_amount     = item.amount
                trans_unit_price = item.unitPrice
                trans_commission = round( item.commission, 2 )
                trans_date       = item.transTime
                trans_value      = trans_amount * trans_unit_price

                currUnitValue = stock_unit_value
                if currUnitValue:
                    currValue = currUnitValue * trans_amount
                    profit    = currValue - trans_value
                    profitPnt = 0
                    if trans_value != 0:
                        profitPnt = profit / trans_value * 100.0
                    profitPnt      = round( profitPnt, 2 )
                    profit         = round( profit, 2 )
                else:
                    currUnitValue = "-"
                    currValue = "-"
                    profit = "-"
                    profitPnt = "-"

                trans_unit_price = round( trans_unit_price, 4 )

                rowsList.append( [ stock_name, ticker, trans_amount, trans_unit_price, trans_commission,
                                   round( trans_value, 2 ), currUnitValue,
                                   profit, profitPnt, trans_date ] )

        dataFrame = DataFrame.from_records( rowsList, columns=columnsList )
        return dataFrame

    def getWalletSellTransactions(self, groupByDay=False) -> DataFrame:
        columnsList = [ "Nazwa", "Ticker", "Liczba",
                        "Kurs K", "Kurs S", "Wartość K", "Wartość S",
                        "Zysk", "Zysk %", "Opłata", "Data K", "Data S" ]

        # currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData
        rowsList = []

        transMode = self.userContainer.transactionsMatchMode

        stock_id: Tuple[ str, str ]
        transactions: TransHistory
        for stock_id, transactions in self.wallet._stockDict.items():
            stock_name: str = stock_id[0] if stock_id else None
            ticker: str     = stock_id[1] if stock_id else None
            if not ticker:
                ticker = ""

            if groupByDay:
                transactions = transactions.groupByDay()

            # currentStockRow = currentStock.getRowByTicker( ticker )
            # stockName = "-"
            # if currentStockRow.empty:
            #     _LOGGER.warning( "could not find stock by ticker: %s", ticker )
            # else:
            #     stockName = currentStockRow["Nazwa"]

            currTransactions = transactions.sellTransactions( transMode )
            if groupByDay:
                newList = []
                currDate  = None
                buyTrans  = Transaction.empty()
                sellTrans = Transaction.empty()
                for buy, sell in currTransactions:
                    transTime = sell.transTime
                    transDate = transTime.date()

                    if transDate != currDate:
                        if sellTrans.isEmpty() is False:
                            newList.append( (buyTrans, sellTrans) )
                        buyTrans  = Transaction.empty()
                        sellTrans = Transaction.empty()

                    currDate = transDate
                    buyTrans.addAvg( buy )
                    sellTrans.addAvg( sell )

                if sellTrans.isEmpty() is False:
                    newList.append( (buyTrans, sellTrans) )
                currTransactions = newList

            for buy, sell in currTransactions:
                trans_amount     = buy.amount
                buy_unit_price   = buy.unitPrice
                sell_unit_price  = sell.unitPrice
                buy_date         = buy.transTime
                sell_date        = sell.transTime

                sellValue = sell_unit_price * trans_amount
                buyValue  = buy_unit_price  * trans_amount
                profit    = sellValue - buyValue
                profitPnt = 0
                if buyValue != 0:
                    profitPnt = profit / buyValue * 100.0

                trans_commission = round( buy.commission + sell.commission, 2 )
                buy_unit_price  = round( buy_unit_price, 4 )
                sell_unit_price = round( sell_unit_price, 4 )
                profitPnt      = round( profitPnt, 2 )
                profit         = round( profit, 2 )

                buyValue = round( buyValue, 2 )
                sellValue = round( sellValue, 2 )

                rowsList.append( [ stock_name, ticker, trans_amount,
                                   buy_unit_price, sell_unit_price, buyValue, sellValue,
                                   profit, profitPnt, trans_commission, buy_date, sell_date ] )

        rowsList.sort( key=lambda x: x[-1], reverse=False )           # sort

        dataFrame = DataFrame.from_records( rowsList, columns=columnsList )
        return dataFrame

    # pylint: disable=R0914
    def getAllTransactions(self, groupByDay=False) -> DataFrame:
        columnsList = [ "Nazwa", "Ticker", "Liczba", "Kurs transakcji", "Opłata", "Wartość",
                        "Kurs aktualny",
                        "Zysk", "Zysk %", "Data transakcji" ]

        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData

        rowsList = []

        for stock_id, transactions in self.wallet._stockDict.items():
            stock_name: str = stock_id[0] if stock_id else None
            ticker: str     = stock_id[1] if stock_id else None

            if groupByDay:
                transactions = transactions.groupByDay()

            stock_unit_value = None
            currentStockRow = currentStock.getRowByTicker( ticker )
            if currentStockRow.empty:
                _LOGGER.warning( "could not find stock by ticker: %s", ticker )
            else:
                stock_unit_value = GpwCurrentStockData.unitPrice( currentStockRow )

            if not ticker:
                ticker = ""

            currAmount = transactions.currentAmount()

            currTransactions = transactions.allTransactions()
            if groupByDay:
                currTransactions = TransHistory.groupTransactionsByDay( currTransactions )

            for item in currTransactions:
                trans_amount     = item.amount
                trans_unit_price = item.unitPrice
                trans_commission = round( item.commission, 2 )
                trans_date       = item.transTime

                currUnitValue = stock_unit_value
                trans_value   = abs( trans_unit_price * trans_amount )

                if currAmount <= 0:
                    ## sell
                    if not currUnitValue:
                        currUnitValue = "-"
                    profitPnt        = "-"
                    profit           = "-"
                else:
                    ## buy
                    if currUnitValue:
                        currValue = abs( currUnitValue * trans_amount )
                        profit    = currValue - trans_value
                        profitPnt = 0
                        if trans_value != 0:
                            profitPnt = profit / trans_value * 100.0
    
                        profit           = round( profit, 2 )
                        profitPnt        = round( profitPnt, 2 )
                    else:
                        currUnitValue = "-"
                        profit    = "-"
                        profitPnt = "-"

                trans_unit_price = round( trans_unit_price, 4 )

                rowsList.append( [ stock_name, ticker, trans_amount, trans_unit_price, trans_commission,
                                   round( trans_value, 2 ), currUnitValue,
                                   profit, profitPnt, trans_date ] )

        dataFrame = DataFrame.from_records( rowsList, columns=columnsList )
        return dataFrame

    def getWalletStockValueData(self, ticker, rangeCode) -> DataFrame:
        transactions: TransHistory = self.wallet.transactions( ticker )
        if transactions is None:
            return None

        isin = self.gpwCurrentData.getStockIsinFromTicker( ticker )
        intraSource = self.gpwStockIntradayData.getSource( isin, rangeCode )
        stockData = intraSource.getWorksheetData()

        startDateTime = stockData.iloc[0, 0]        ## first date
        startDate = startDateTime.date()

        transList = transactions.transactionsAfter( startDate )

        amountBefore = transactions.amountBeforeDate( startDate )
        dataFrame = stockData[ ["t", "c"] ].copy()

        rowsNum    = dataFrame.shape[0]
        rowIndex   = 0
        currAmount = amountBefore

        for item in reversed( transList ):
            transTime = item.transTime
            while rowIndex < rowsNum:
                if dataFrame.at[ rowIndex, "t" ] < transTime:
                    dataFrame.at[ rowIndex, "c" ] = dataFrame.at[ rowIndex, "c" ] * currAmount
                    rowIndex += 1
                else:
                    break
            currAmount += item.amount

        while rowIndex < rowsNum:
            dataFrame.at[ rowIndex, "c" ] = dataFrame.at[ rowIndex, "c" ] * currAmount
            rowIndex += 1

        return dataFrame

    ## wallet summary: wallet value, wallet profit, ref change, gain, overall profit
    def getWalletState(self):
        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData

        transMode = self.userContainer.transactionsMatchMode

        walletValue    = 0.0
        refWalletValue = 0.0
        walletProfit   = 0.0
        totalGain      = 0.0
        for stock_id, tickerTransactions in self.wallet._stockDict.items():
            ticker = stock_id[1] if stock_id else None
            amount, buy_unit_price = tickerTransactions.currentTransactionsAvg( transMode )

            stockGain  = tickerTransactions.transactionsGain( transMode, True )
            totalGain += stockGain

            if amount == 0:
                continue

            currentStockRow = currentStock.getRowByTicker( ticker )
            if currentStockRow is None or currentStockRow.empty:
                _LOGGER.warning( "could not find stock by ticker: %s", ticker )
                continue

            currUnitValue = GpwCurrentStockData.unitPrice( currentStockRow )

            sellValue      = currUnitValue * amount             ## amount is positive
            sellValue     -= broker_commission( sellValue )
            buyValue       = buy_unit_price * amount

#             _LOGGER.info( "wallet state: %s %s %s %s", ticker, amount, currUnitValue, sellValue )

            walletValue   += sellValue
            walletProfit  += sellValue - buyValue

            refUnitValue  = GpwCurrentStockData.unitReferencePrice( currentStockRow )
            referenceValue = refUnitValue * amount
            refWalletValue += referenceValue

        walletValue    = round( walletValue, 2 )
        walletProfit   = round( walletProfit, 2 )
        refWalletValue = round( refWalletValue, 2 )
        if refWalletValue != 0.0:
            referenceFactor = walletValue / refWalletValue - 1
            rounded_factor = round( referenceFactor * 100, 2 )
            changeToRef = f"{rounded_factor}%"
        else:
            changeToRef = "--"
        totalGain      = round( totalGain, 2 )
        overallProfit  = walletProfit + totalGain
        overallProfit  = round( overallProfit, 2 )
        return ( walletValue, walletProfit, changeToRef, totalGain, overallProfit )

    ## =========================================================================

    ## returns DataFrame with two columns: 't' (timestamp) and 'c' (value)
    def getWalletValueHistory(self, rangeCode) -> DataFrame:
        mergedList = None
        for ticker in self.wallet.tickers():
            stockData = self.getWalletStockValueHistory( ticker, rangeCode )
            if stockData is None:
                continue
#             _LOGGER.info( "wallet state: %s %s", ticker, stockData.iloc[ -1, 1 ] )
            mergedList = join_list_dataframe( mergedList, stockData )

        retData = DataFrame( mergedList, columns=["t", "c"] )
        return retData

    ## calculate value of single stock
    def getWalletStockValueHistory( self, ticker, rangeCode ) -> DataFrame:
        transactions: TransHistory = self.wallet.transactions( ticker )
        if transactions is None:
            return None

        isin        = self.gpwCurrentData.getStockIsinFromTicker( ticker )
        intraSource = self.gpwStockIntradayData.getSource( isin, rangeCode )
        stockData   = intraSource.getWorksheetData()
        if stockData is None:
            return None

        return transactions.calculateValueHistory( stockData )

    ## returns DataFrame with two columns: 't' (timestamp) and 'c' (value)
    def getWalletGainHistory(self, rangeCode) -> DataFrame:
        startDateTime = get_start_date( rangeCode )

        transMode = self.userContainer.transactionsMatchMode
        mergedList = None
        for _, transactions in self.wallet._stockDict.items():
            gainList = transactions.transactionsGainHistory( transMode, True, startDateTime )
            stockData = DataFrame( gainList, columns=["t", "c"] )
            mergedList = join_list_dataframe( mergedList, stockData )

        retData = DataFrame( mergedList, columns=["t", "c"] )
        return retData

    ## returns DataFrame with two columns: 't' (timestamp) and 'c' (value)
    def getWalletProfitHistory(self, rangeCode, calculateOverall: bool = True) -> DataFrame:
        mergedList = None
        for ticker in self.wallet.tickers():
            stockData = self.getWalletStockProfitHistory( ticker, rangeCode, calculateOverall )
            if stockData is None:
                continue
            mergedList = join_list_dataframe( mergedList, stockData )

        retData = DataFrame( mergedList, columns=["t", "c"] )
        return retData

    ## calculate profit of single stock
    def getWalletStockProfitHistory(self, ticker, rangeCode, calculateOverall: bool = True) -> DataFrame:
        transactions: TransHistory = self.wallet.transactions( ticker )
        if transactions is None:
            return None

        isin = self.gpwCurrentData.getStockIsinFromTicker( ticker )
        intraSource = self.gpwStockIntradayData.getSource( isin, rangeCode )
        stockData = intraSource.getWorksheetData()
        if stockData is None:
            return None

        transMode = self.userContainer.transactionsMatchMode
        return transactions.calculateProfitHistory( stockData, transMode, calculateOverall )

    ## =========================================================================

    def loadDownloadedStocks(self):
        stockList = self.refreshAllList()
        for func, args in stockList:
            func( *args )

    def refreshStockList(self, forceRefresh=False):
        stockList: List[ StockDataProvider ] = self._dataStockProvidersList()
        retList = []
        for stock in stockList:
            retList.append( (stock.accessData, [forceRefresh] ) )
        return retList

    def refreshAllList(self, forceRefresh=False, access=True):
        stockList: List[ StockDataProvider ] = self._dataAllProvidersList()
        retList = []
        for stock in stockList:
            if access:
                retList.append( (stock.accessData, [forceRefresh] ) )
            else:
                retList.append( (stock.getData, [forceRefresh] ) )
        return retList

    def _dataAllProvidersList(self) -> List[ StockDataProvider ]:
#         retList = []
#         retList.append( self.gpwCurrentSource )
#         retList.append( self.gpwStockIntradayData )
#         retList.append( self.gpwIndexIntradayData )
#         retList.append( BaseWorksheetDAOProvider( self.gpwESPIData ) )
#         retList.append( BaseWorksheetDAOProvider( self.gpwIndexesData ) )

        retList = self._dataStockProvidersList()

        retList.append( BaseWorksheetDAOProvider( self.globalIndexesData ) )
        retList.append( BaseWorksheetDAOProvider( self.gpwIndicatorsData ) )
        retList.append( BaseWorksheetDAOProvider( self.gpwDividendsData ) )
        retList.append( BaseWorksheetDAOProvider( self.gpwReportsData ) )
        retList.append( BaseWorksheetDAOProvider( self.gpwPubReportsData ) )
        retList.append( BaseWorksheetDAOProvider( self.gpwCurrentShortSellingsData ) )
#         retList.append( self.gpwIsinMap )
        return retList

    def _dataStockProvidersList(self) -> List[ StockDataProvider ]:
        retList = []
        retList.append( self.gpwCurrentSource )

        ## do not refresh charts
#         retList.append( self.gpwStockIntradayData )
#         retList.append( self.gpwIndexIntradayData )

        retList.append( BaseWorksheetDAOProvider( self.gpwESPIData ) )
        retList.append( BaseWorksheetDAOProvider( self.gpwIndexesData ) )
        return retList

    @property
    def gpwCurrentHeaders(self) -> Dict[ int, str ]:
        return self.gpwCurrentSource.stockHeaders

    @property
    def gpwCurrentData(self) -> GpwCurrentStockData:
        return self.gpwCurrentSource.stockData                  # type: ignore

#     def getStockIntradayDataByTicker(self, ticker):
#         isin = self.gpwCurrentData.getStockIsinFromTicker(ticker)
#         return self.gpwStockIntradayData.getData(isin)

#     def getStockIntradayDataByIsin(self, isin):
#         return self.gpwStockIntradayData.getData(isin)

#     def getIndexIntradayDataByIsin(self, isin):
#         return self.gpwIndexIntradayData.getData(isin)


## stockData contains two columns: 't' and 'c'
def join_list_dataframe( mergedList, stockData: DataFrame ):
    if mergedList is None:
        return stockData.values.tolist()

    mSize = len( mergedList )
    if mSize < 1:
        return stockData.values.tolist()

    stockSize = stockData.shape[0]
    if stockSize < 1:
        return mergedList

    ## merge data frames
    newList = []

    m = 0
    s = 0
    while m < mSize and s < stockSize:
        currTime  = mergedList[ m ][ 0 ]
        stockTime = stockData.at[ s, "t" ]
        if stockTime < currTime:
            if m > 0:
                prevIndex = max( m - 1, 0 )
                newValue = mergedList[ prevIndex ][ 1 ] + stockData.at[ s, "c" ]
                rowList = [ stockTime, newValue ]
                newList.append( rowList )
                s += 1
            else:
                newValue = stockData.at[ s, "c" ]
                rowList = [ stockTime, newValue ]
                newList.append( rowList )
                s += 1
        elif stockTime == currTime:
            newValue = mergedList[ m ][ 1 ] + stockData.at[ s, "c" ]
            rowList = [ stockTime, newValue ]
            newList.append( rowList )
            m += 1
            s += 1
        else:
            ## stockTime > currTime
            if s > 0:
                prevIndex = max( s - 1, 0 )
                newValue = mergedList[ m ][ 1 ] + stockData.at[ prevIndex, "c" ]
                rowList = [ currTime, newValue ]
                newList.append( rowList )
                m += 1
            else:
                newValue = mergedList[ m ][ 1 ]
                rowList = [ currTime, newValue ]
                newList.append( rowList )
                m += 1

    ## join rest of stockData
    lastValue = mergedList[ mSize - 1][1]
    while s < stockSize:
        stockTime = stockData.at[ s, "t" ]
        newValue = stockData.at[ s, "c" ] + lastValue
        rowList = [ stockTime, newValue ]
        newList.append( rowList )
        s += 1

    ## join rest of mergedList
    lastValue = stockData.at[ stockSize - 1, "c" ]
    while m < mSize:
        currTime  = mergedList[ m ][ 0 ]
        newValue = mergedList[ m ][ 1 ] + lastValue
        rowList = [ currTime, newValue ]
        newList.append( rowList )
        m += 1

    return newList


def get_start_date( rangeCode ):
    startDateTime = datetime.datetime.now()      # datetime
    if rangeCode == "1D":
        startDateTime -= datetime.timedelta( days=1 )
    elif rangeCode == "14D":
        startDateTime -= datetime.timedelta( days=14 )
    elif rangeCode == "1M":
        startDateTime -= datetime.timedelta( days=31 )
    elif rangeCode == "3M":
        startDateTime -= datetime.timedelta( weeks=13 )
    elif rangeCode == "6M":
        startDateTime -= datetime.timedelta( weeks=26 )
    elif rangeCode == "1R":
        startDateTime -= datetime.timedelta( weeks=52 )
    elif rangeCode == "2R":
        startDateTime -= datetime.timedelta( weeks=104 )
    elif rangeCode == "3R":
        startDateTime -= datetime.timedelta( weeks=156 )
    elif rangeCode == "MAX":
        curr_time  = startDateTime.time()
        start_date = datetime.date( year=1991, month=4, day=16 )                ## first day of stock
        startDateTime = datetime.datetime.combine( start_date, curr_time )
    else:
        _LOGGER.warning( "unknown range code: %s", rangeCode )
        startDateTime = None
    return startDateTime
