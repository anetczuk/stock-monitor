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
from typing import Dict

from datetime import datetime

from pandas.core.frame import DataFrame

from stockmonitor import persist
from stockmonitor.dataaccess.gpw.gpwdata import GpwIndicatorsData
from stockmonitor.dataaccess.dividendsdata import DividendsCalendarData
from stockmonitor.dataaccess.finreportscalendardata import PublishedFinRepsCalendarData, FinRepsCalendarData
from stockmonitor.dataaccess.globalindexesdata import GlobalIndexesData
from stockmonitor.dataaccess.gpw.gpwcurrentdata import GpwCurrentStockData, GpwCurrentIndexesData
from stockmonitor.dataaccess.gpw.gpwespidata import GpwESPIData

from stockmonitor.datatypes.datatypes import UserContainer,\
    FavData, WalletData, MarkersContainer, MarkerEntry
from stockmonitor.datatypes.stocktypes import StockData, GpwStockIntradayMap,\
    GpwIndexIntradayMap
from stockmonitor.datatypes.wallettypes import broker_commission, TransHistory


_LOGGER = logging.getLogger(__name__)


##
##
##
class DataContainer():

    def __init__(self):
        self.userContainer        = UserContainer()                   ## user data

        self.gpwCurrentSource     = StockData( GpwCurrentStockData() )
        self.gpwStockIntradayData = GpwStockIntradayMap()
        self.gpwIndexIntradayData = GpwIndexIntradayMap()

        self.gpwESPIData        = GpwESPIData()

        self.gpwIndexesData     = GpwCurrentIndexesData()
        self.globalIndexesData  = GlobalIndexesData()
        self.gpwIndicatorsData  = GpwIndicatorsData()
        self.gpwDividendsData   = DividendsCalendarData()

        self.gpwReportsData     = FinRepsCalendarData()
        self.gpwPubReportsData  = PublishedFinRepsCalendarData()

#         self.gpwIsinMap         = GpwIsinMapData()

    def store( self, outputDir ):
        outputFile = outputDir + "/gpwcurrentheaders.obj"
        persist.store_object( self.gpwCurrentHeaders, outputFile )
        return self.userContainer.store( outputDir )

    def load( self, inputDir ):
        self.userContainer.load( inputDir )
        inputFile = inputDir + "/gpwcurrentheaders.obj"
        headers = persist.load_object_simple( inputFile, dict() )
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
        columnsList = [ "Nazwa", "Ticker", "Typ operacji", "Kurs operacji", "Liczba", "Kolor", "Uwagi" ]
        rowsList = []
        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData
        mSize = self.markers.size()
        for i in range(0, mSize):
            entry: MarkerEntry = self.markers.get( i )
            stockName = currentStock.getNameFromTicker( entry.ticker )
            rowDict = {}
            rowDict[ columnsList[ 0] ] = stockName
            rowDict[ columnsList[ 1] ] = entry.ticker
            rowDict[ columnsList[ 2] ] = entry.operationName()
            rowDict[ columnsList[ 3] ] = entry.value
            rowDict[ columnsList[ 4] ] = entry.amount
            rowDict[ columnsList[ 5] ] = entry.color
            if entry.notes is not None:
                rowDict[ columnsList[ 6] ] = entry.notes
            else:
                rowDict[ columnsList[ 6] ] = ""
            rowsList.append( rowDict )

        dataFrame = DataFrame( rowsList )
        dataFrame = dataFrame.fillna("-")
        return dataFrame

    ## ======================================================================

    def transactionsMatchMode(self):
        return self.userContainer.transactionsMatchMode

    ## ======================================================================

    def importWalletTransactions(self, dataFrame: DataFrame, addTransactions=False):
#         wallet: WalletData = self.wallet
        importWallet = WalletData()

        for _, row in dataFrame.iterrows():
            transTime  = row['trans_time']
            stockName  = row['name']
            oper       = row['k_s']
            amount     = row['amount']
            unit_price = row['unit_price']

#             print("raw row:", transTime, stockName, oper, amount, unit_price)

            dateObject = None
            try:
                ## 31.03.2020 13:21:44
                dateObject = datetime.strptime(transTime, '%d.%m.%Y %H:%M:%S')
            except ValueError:
                dateObject = None

            ticker = self.getTickerFromName( stockName )
            if ticker is None:
                _LOGGER.warning( "could not find stock ticker for name: >%s<", stockName )
                continue

            if oper == "K":
                importWallet.add( ticker,  amount, unit_price, dateObject, False )
            elif oper == "S":
                importWallet.add( ticker, -amount, unit_price, dateObject, False )

        if addTransactions:
            ## merge wallets
            self.wallet.addWallet( importWallet )
        else:
            ## replace wallet
            self.userContainer.wallet = importWallet

        self.updateWalletFavGroup()

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
    def getWalletStock(self):
        columnsList = [ "Nazwa", "Ticker", "Liczba", "Kurs", "Zm.do k.odn.[%]",
                        "Średni kurs nabycia", "Wartość [PLN]", "Zm.do k.odn.[PLN]", "Udział [%]",
                        "Zysk [PLN]", "Zysk [%]", "Zysk całkowity [PLN]" ]
        # apply_on_column( dataFrame, 'Zm.do k.odn.(%)', convert_float )

        walletState = self.getWalletState()
        walletValue = walletState[0]

        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData
        rowsList = []

        transMode = self.userContainer.transactionsMatchMode

        for ticker, transactions in self.wallet.stockList.items():
            amount, buy_unit_price = transactions.currentTransactionsAvg( transMode )
            currentStockRow = currentStock.getRowByTicker( ticker )

            if currentStockRow.empty:
                _LOGGER.warning( "could not find stock by ticker: %s", ticker )
                rowDict = {}
                rowDict[ columnsList[ 0] ] = "-"
                rowDict[ columnsList[ 1] ] = ticker
                rowDict[ columnsList[ 2] ] = amount
                rowDict[ columnsList[ 3] ] = buy_unit_price
                rowDict[ columnsList[ 4] ] = "-"
                rowDict[ columnsList[ 5] ] = "-"
                rowDict[ columnsList[ 6] ] = "-"
                rowDict[ columnsList[ 7] ] = "-"
                rowDict[ columnsList[ 8] ] = "-"
                rowDict[ columnsList[ 9] ] = "-"
                rowDict[ columnsList[10] ] = "-"
                rowDict[ columnsList[11] ] = "-"
                rowsList.append( rowDict )
                continue

            stockName = currentStockRow["Nazwa"]

            currUnitValue = GpwCurrentStockData.unitPrice( currentStockRow )

            currChangeRaw = currentStockRow.iloc[ 12 ]
            currChangePnt = 0
            if currChangeRaw != "-":
                currChangePnt = float( currChangeRaw )

            currValue = currUnitValue * amount

            ## ( curr_unit_price - ref_unit_price ) * unit_price * amount
            valueChange = currChangePnt / 100.0 * currValue

            participation = currValue / walletValue * 100.0

            buyValue  = buy_unit_price * amount
            profit    = currValue - buyValue
            profitPnt = 0
            if buyValue != 0:
                profitPnt = profit / buyValue * 100.0

            totalProfit  = transactions.transactionsProfit()
            totalProfit += currValue - broker_commission( currValue )

            rowDict = {}
            rowDict[ columnsList[ 0] ] = stockName
            rowDict[ columnsList[ 1] ] = ticker
            rowDict[ columnsList[ 2] ] = amount
            rowDict[ columnsList[ 3] ] = round( currUnitValue, 2 )
            rowDict[ columnsList[ 4] ] = round( currChangePnt, 2 )
            rowDict[ columnsList[ 5] ] = round( buy_unit_price, 4 )
            rowDict[ columnsList[ 6] ] = round( currValue, 2 )
            rowDict[ columnsList[ 7] ] = round( valueChange, 2 )
            rowDict[ columnsList[ 8] ] = round( participation, 2 )
            rowDict[ columnsList[ 9] ] = round( profit, 2 )
            rowDict[ columnsList[10] ] = round( profitPnt, 2 )
            rowDict[ columnsList[11] ] = round( totalProfit, 2 )
            rowsList.append( rowDict )

        dataFrame = DataFrame( rowsList )
        return dataFrame

    ## wallet summary: wallet value, wallet profit, gain, overall profit
    def getWalletState(self, includeCommission=True):
        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData

        transMode = self.userContainer.transactionsMatchMode

        walletValue    = 0.0
        refWalletValue = 0.0
        walletProfit   = 0.0
        totalGain      = 0.0
        for ticker, transactions in self.wallet.stockList.items():
            amount, buy_unit_price = transactions.currentTransactionsAvg( transMode )

            stockGain  = transactions.transactionsGain( transMode, includeCommission )
            totalGain += stockGain

            if amount == 0:
                continue

            tickerRow = currentStock.getRowByTicker( ticker )
            if tickerRow.empty:
                _LOGGER.warning( "could not find stock by ticker: %s", ticker )
                continue

            currUnitValue = GpwCurrentStockData.unitPrice( tickerRow )

            stockValue     = currUnitValue * amount
            stockProfit    = stockValue
            stockProfit   -= buy_unit_price * amount
            if includeCommission:
                stockProfit -= broker_commission( stockValue )

            walletValue   += stockValue
            walletProfit  += stockProfit

            refUnitValue  = GpwCurrentStockData.unitReferencePrice( tickerRow )
            referenceValue = refUnitValue * amount
            refWalletValue += referenceValue

        walletValue    = round( walletValue, 2 )
        walletProfit   = round( walletProfit, 2 )
        refWalletValue = round( refWalletValue, 2 )
        if refWalletValue != 0.0:
            referenceFactor = walletValue / refWalletValue - 1
            changeToRef = "%s%%" % round( referenceFactor * 100, 2 )
        else:
            changeToRef = "--"
        totalGain      = round( totalGain, 2 )
        overallProfit  = walletProfit + totalGain
        overallProfit  = round( overallProfit, 2 )
        return ( walletValue, walletProfit, changeToRef, totalGain, overallProfit )

    # pylint: disable=R0914
    def getWalletBuyTransactions(self):
        columnsList = [ "Nazwa", "Ticker", "Liczba", "Kurs transakcji",
                        "Kurs", "Zm.do k.odn.(%)",
                        "Zysk %", "Zysk", "Data transakcji" ]

        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData
        rowsList = []

        transMode = self.userContainer.transactionsMatchMode

        ticker: str
        transactions: TransHistory
        for ticker, transactions in self.wallet.stockList.items():
#             if ticker == "PCX":
#                 print( "xxxxx:\n", transactions.items() )
            currentStockRow = currentStock.getRowByTicker( ticker )
            if currentStockRow.empty:
                _LOGGER.warning( "could not find stock by ticker: %s", ticker )
                currTransactions = transactions.currentTransactions( transMode )
                for item in currTransactions:
                    trans_amount     = item[0]
                    trans_unit_price = item[1]
                    trans_date       = item[2]
                    rowsList.append( ["-", ticker, trans_amount, trans_unit_price, "-", "-", "-", "-", trans_date] )
                continue

            currUnitValue = GpwCurrentStockData.unitPrice( currentStockRow )

            currChangeRaw = currentStockRow.iloc[ 12 ]
            currChange    = 0
            if currChangeRaw != "-":
                currChange = float( currChangeRaw )

            currTransactions = transactions.currentTransactions( transMode )
            for item in currTransactions:
                stockName = currentStockRow["Nazwa"]

                trans_amount     = item[0]
                trans_unit_price = item[1]
                trans_date       = item[2]

                currValue = currUnitValue * trans_amount
                buyValue  = trans_unit_price * trans_amount
                profit    = currValue - buyValue
                profitPnt = 0
                if buyValue != 0:
                    profitPnt = profit / buyValue * 100.0

                trans_unit_price = round( trans_unit_price, 4 )
                profitPnt      = round( profitPnt, 2 )
                profit         = round( profit, 2 )

                rowsList.append( [ stockName, ticker, trans_amount, trans_unit_price,
                                   currUnitValue, currChange,
                                   profitPnt, profit, trans_date ] )

        dataFrame = DataFrame.from_records( rowsList, columns=columnsList )
        return dataFrame

    def getWalletSellTransactions(self):
        columnsList = [ "Nazwa", "Ticker", "Liczba", "Kurs kupna",
                        "Kurs sprzedaży", "Zm.do k.odn.(%)",
                        "Zysk %", "Zysk", "Data transakcji" ]

        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData
        rowsList = []

        transMode = self.userContainer.transactionsMatchMode

        ticker: str
        transactions: TransHistory
        for ticker, transactions in self.wallet.stockList.items():
#             if ticker == "PCX":
#                 print( "xxxxx:\n", transactions.items() )
            currentStockRow = currentStock.getRowByTicker( ticker )
            if currentStockRow.empty:
                _LOGGER.warning( "could not find stock by ticker: %s", ticker )
                currTransactions = transactions.sellTransactions( transMode )
                for buy, sell in currTransactions:
                    trans_amount     = buy[0]
                    trans_unit_price = buy[1]
                    trans_date       = buy[2]
                    rowsList.append( ["-", ticker, trans_amount, trans_unit_price, "-", "-", "-", "-", trans_date] )
                continue

            currChange    = "-"

            currTransactions = transactions.sellTransactions( transMode )
            for buy, sell in currTransactions:
                stockName = currentStockRow["Nazwa"]

                trans_amount    = buy[0]
                buy_unit_price  = buy[1]
                sell_unit_price = sell[1]
                sell_date       = sell[2]

                currValue = sell_unit_price * trans_amount
                buyValue  = buy_unit_price * trans_amount
                profit    = currValue - buyValue
                profitPnt = 0
                if buyValue != 0:
                    profitPnt = profit / buyValue * 100.0

                buy_unit_price = round( buy_unit_price, 4 )
                profitPnt      = round( profitPnt, 2 )
                profit         = round( profit, 2 )

                rowsList.append( [ stockName, ticker, -trans_amount, buy_unit_price,
                                   sell_unit_price, currChange,
                                   profitPnt, profit, sell_date ] )

        dataFrame = DataFrame.from_records( rowsList, columns=columnsList )
        return dataFrame

    # pylint: disable=R0914
    def getAllTransactions(self):
        columnsList = [ "Nazwa", "Ticker", "Liczba", "Kurs transakcji",
                        "Kurs", "Zm.do k.odn.(%)",
                        "Zysk %", "Zysk", "Data transakcji" ]

        currentStock: GpwCurrentStockData = self.gpwCurrentSource.stockData
        rowsList = []

        for ticker, transactions in self.wallet.stockList.items():
            currentStockRow = currentStock.getRowByTicker( ticker )
            if currentStockRow.empty:
                _LOGGER.warning( "could not find stock by ticker: %s", ticker )
                currTransactions = transactions.allTransactions()
                for item in currTransactions:
                    trans_amount     = item[0]
                    trans_unit_price = item[1]
                    trans_date       = item[2]
                    rowsList.append( ["-", ticker, trans_amount, trans_unit_price, "-", "-", "-", "-", trans_date] )
                continue

            currAmount = transactions.currentAmount()

            currUnitValue = GpwCurrentStockData.unitPrice( currentStockRow )

            currChangeRaw = currentStockRow.iloc[ 12 ]
            currChange    = 0
            if currChangeRaw != "-":
                currChange = float( currChangeRaw )

            currTransactions = transactions.allTransactions()
            for item in currTransactions:
                stockName = currentStockRow["Nazwa"]

                trans_amount     = item[0]
                trans_unit_price = item[1]
                trans_date       = item[2]

                if currAmount <= 0:
                    trans_unit_price = round( trans_unit_price, 4 )
                    profitPnt        = "-"
                    profit           = "-"
                else:
                    currValue = abs( currUnitValue * trans_amount )
                    buyValue  = abs( trans_unit_price * trans_amount )

                    profit    = currValue - buyValue
                    profitPnt = 0
                    if buyValue != 0:
                        profitPnt = profit / buyValue * 100.0

                    trans_unit_price = round( trans_unit_price, 4 )
                    profitPnt        = round( profitPnt, 2 )
                    profit           = round( profit, 2 )

                rowsList.append( [ stockName, ticker, trans_amount, trans_unit_price,
                                   currUnitValue, currChange,
                                   profitPnt, profit, trans_date ] )

        dataFrame = DataFrame.from_records( rowsList, columns=columnsList )
        return dataFrame

    def getWalletStockValueData(self, ticker, rangeCode):
        transactions: TransHistory = self.wallet.transactions( ticker )
        if transactions is None:
            return None

        isin = self.getStockIsinFromTicker( ticker )
        intraSource = self.gpwStockIntradayData.getSource( isin, rangeCode )
        stockData = intraSource.getWorksheet()

        startDateTime = stockData.iloc[0, 0]        ## first date
        startDate = startDateTime.date()

        transList = transactions.transactionsAfter( startDate )

        amountBefore = transactions.amountBeforeDate( startDate )
        dataFrame = stockData[ ["t", "c"] ].copy()

        rowsNum    = dataFrame.shape[0]
        rowIndex   = 0
        currAmount = amountBefore

        for item in reversed( transList ):
            transTime = item[2]
            while rowIndex < rowsNum:
                if dataFrame.at[ rowIndex, "t" ] < transTime:
                    dataFrame.at[ rowIndex, "c" ] = dataFrame.at[ rowIndex, "c" ] * currAmount
                    rowIndex += 1
                else:
                    break
            currAmount += item[0]

        while rowIndex < rowsNum:
            dataFrame.at[ rowIndex, "c" ] = dataFrame.at[ rowIndex, "c" ] * currAmount
            rowIndex += 1

        return dataFrame

    def getWalletStockProfitData(self, ticker, rangeCode):
        transactions: TransHistory = self.wallet.transactions( ticker )
        if transactions is None:
            return None

        isin = self.getStockIsinFromTicker( ticker )
        intraSource = self.gpwStockIntradayData.getSource( isin, rangeCode )
        stockData = intraSource.getWorksheet()
        if stockData is None:
            return None

        startDateTime = stockData.iloc[0, 0]        ## first date
        startDate = startDateTime.date()

        transBefore  = transactions.transactionsBefore( startDate )
        pendingTrans = transactions.transactionsAfter( startDate )

        dataFrame = stockData[ ["t", "c"] ].copy()
        rowsNum   = dataFrame.shape[0]
        rowIndex  = 0

        for item in reversed( pendingTrans ):
            transTime = item[2]
            amountBefore = transBefore.currentAmount()
            totalProfit  = transBefore.transactionsProfit()
            while rowIndex < rowsNum:
                stockTime = dataFrame.at[ rowIndex, "t" ]
                if stockTime < transTime:
                    if amountBefore > 0:
                        profit = totalProfit - broker_commission( amountBefore, stockTime )
                        dataFrame.at[ rowIndex, "c" ] = dataFrame.at[ rowIndex, "c" ] * amountBefore + profit
                    else:
                        dataFrame.at[ rowIndex, "c" ] = totalProfit
                    rowIndex += 1
                else:
                    break
            transBefore.appendItem( item )

        amountBefore = transBefore.currentAmount()
        totalProfit  = transBefore.transactionsProfit()
        while rowIndex < rowsNum:
            stockTime = dataFrame.at[ rowIndex, "t" ]
            if amountBefore > 0:
                profit = totalProfit - broker_commission( amountBefore, stockTime )
                dataFrame.at[ rowIndex, "c" ] = dataFrame.at[ rowIndex, "c" ] * amountBefore + profit
            else:
                dataFrame.at[ rowIndex, "c" ] = totalProfit
            rowIndex += 1

        return dataFrame

    def getWalletTotalProfitData(self, rangeCode):
        mergedList = None
        for ticker in self.wallet.tickers():
            stockData = self.getWalletStockProfitData( ticker, rangeCode )
            if stockData is None:
                continue
            if mergedList is None:
                mergedList = stockData.values.tolist()
                continue

            retSize = len( mergedList )
            if retSize < 1:
                mergedList = stockData.values.tolist()
                continue

            stockSize = stockData.shape[0]
            if stockSize < 1:
                continue

            ## merge data frames
            newList = []

            i = 0
            j = 0
            while i < retSize and j < stockSize:
                currTime  = mergedList[ i ][ 0 ]
                stockTime = stockData.at[ j, "t" ]
                if stockTime < currTime:
                    prevIndex = max( i - 1, 0 )
                    newValue = mergedList[ prevIndex ][ 1 ] + stockData.at[ j, "c" ]
                    rowList = [ stockTime, newValue ]
                    newList.append( rowList )
                    j += 1
                elif stockTime == currTime:
                    newValue = mergedList[ i ][ 1 ] + stockData.at[ j, "c" ]
                    rowList = [ stockTime, newValue ]
                    newList.append( rowList )
                    i += 1
                    j += 1
                else:
                    prevIndex = max( j - 1, 0 )
                    newValue = mergedList[ i ][ 1 ] + stockData.at[ prevIndex, "c" ]
                    rowList = [ currTime, newValue ]
                    newList.append( rowList )
                    i += 1

            lastStockValue = stockData.at[ stockSize - 1, "c" ]
            while i < retSize:
                currTime  = mergedList[ i ][ 0 ]
                newValue = mergedList[ i ][ 1 ] + lastStockValue
                rowList = [ currTime, newValue ]
                newList.append( rowList )
                i += 1

            mergedList = newList

        retData = DataFrame( mergedList, columns=["t", "c"] )
        return retData

    ## ======================================================================

    def loadDownloadedStocks(self):
        stockList = self.refreshAllList()
        for func, args in stockList:
            func( *args )

    def refreshStockList(self, forceRefresh=False):
        stockList = self.dataStockProvidersList()
        retList = []
        for stock in stockList:
            retList.append( (stock.refreshData, [forceRefresh] ) )
        return retList

    def refreshAllList(self, forceRefresh=False):
        stockList = self.dataAllProvidersList()
        retList = []
        for stock in stockList:
            retList.append( (stock.refreshData, [forceRefresh] ) )
        return retList

#     def stockDownloadList(self):
#         stockList = self.dataAllProvidersList()
#         retList = []
#         for stock in stockList:
#             retList.append( stock.downloadData )
#         return retList

    def dataAllProvidersList(self):
        retList = []
        retList.append( self.gpwCurrentSource )
        retList.append( self.gpwStockIntradayData )
        retList.append( self.gpwIndexIntradayData )
        retList.append( self.gpwESPIData )
        retList.append( self.gpwIndexesData )
        retList.append( self.globalIndexesData )
        retList.append( self.gpwIndicatorsData )
        retList.append( self.gpwDividendsData )
        retList.append( self.gpwReportsData )
        retList.append( self.gpwPubReportsData )
#         retList.append( self.gpwIsinMap )
        return retList

    def dataStockProvidersList(self):
        retList = []
        retList.append( self.gpwCurrentSource )
        retList.append( self.gpwStockIntradayData )
        retList.append( self.gpwIndexIntradayData )
        retList.append( self.gpwESPIData )
        retList.append( self.gpwIndexesData )
        return retList

    @property
    def gpwCurrentHeaders(self) -> Dict[ int, str ]:
        return self.gpwCurrentSource.stockHeaders

    @property
    def gpwCurrentData(self) -> GpwCurrentStockData:
        return self.gpwCurrentSource.stockData                  # type: ignore

    def getStockIntradayDataByTicker(self, ticker):
        isin = self.getStockIsinFromTicker(ticker)
        return self.gpwStockIntradayData.getData(isin)

    def getStockIntradayDataByIsin(self, isin):
        return self.gpwStockIntradayData.getData(isin)

    def getIndexIntradayDataByIsin(self, isin):
        return self.gpwIndexIntradayData.getData(isin)

    def getTicker(self, rowIndex):
        return self.gpwCurrentSource.stockData.getTickerField( rowIndex )

    def getTickerFromIsin(self, stockIsin):
        return self.gpwCurrentData.getTickerFromIsin( stockIsin )

    def getTickerFromName(self, stockName):
        return self.gpwCurrentData.getTickerFromName( stockName )

    def getStockIsinFromTicker(self, ticker):
        return self.gpwCurrentData.getStockIsinFromTicker( ticker )

    def getNameFromTicker(self, ticker):
        return self.gpwCurrentData.getNameFromTicker( ticker )
