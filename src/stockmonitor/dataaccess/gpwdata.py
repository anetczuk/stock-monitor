'''
Created on Apr 12, 2020

@author: bob
'''

import os
import logging
import urllib.request
from datetime import date

import xlrd
import datetime


_LOGGER = logging.getLogger(__name__)


class GpwCrawler:
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''

    
    ## Brak danych dla wybranych kryteriów.
    
    def getStockData(self, day):
        file = "./../tmp/data/gpw/" + day.strftime("%Y-%m-%d") + ".xls"
        if os.path.exists( file ):
            return file
        
        ## pattern example: https://www.gpw.pl/archiwum-notowan?fetch=1&type=10&instrument=&date=15-01-2020
        url = "https://www.gpw.pl/archiwum-notowan?fetch=1&type=10&instrument=&date=" + day.strftime("%d-%m-%Y")
        _LOGGER.debug( "grabbing data from utl: %s", url )

        dirPath = os.path.dirname( file )
        os.makedirs( dirPath, exist_ok=True )
        urllib.request.urlretrieve( url, file )
        return file


class GpwData:
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.crawler = GpwCrawler()
        
    def getMax(self, day: date):
        _LOGGER.debug( "getting max from date: %s", day )
        worksheet = self.getWorksheet(day)
        if worksheet is None:
            return None
        # min col index: 5
        return self.extractColumn( worksheet, 5 )
        
    def getMin(self, day: date):
        _LOGGER.debug( "getting min from date: %s", day )
        worksheet = self.getWorksheet(day)
        if worksheet is None:
            return None
        # min col index: 6
        return self.extractColumn( worksheet, 6 )
        
    def getClose(self, day: date):
        _LOGGER.debug( "getting date: %s", day )
        worksheet = self.getWorksheet(day)
        if worksheet is None:
            return None
        # close col index: 7
        return self.extractColumn( worksheet, 7 )
        
    def getVolume(self, day: date):
        _LOGGER.debug( "getting date: %s", day )
        worksheet = self.getWorksheet(day)
        if worksheet is None:
            return None
        # volume col index: 9
        return self.extractColumn( worksheet, 9 )
        
    def getTurnover(self, day: date):
        _LOGGER.debug( "getting date: %s", day )
        worksheet = self.getWorksheet(day)
        if worksheet is None:
            return None
        # turnover col index: 11
        return self.extractColumn( worksheet, 11 )
    
    def getLastValidDay(self, day: date):
        currDay = day
        worksheet = None
        while True:
            worksheet = self.getWorksheet(currDay)
            if worksheet is not None:
                break
            currDay -= datetime.timedelta(days=1)
        # close col index: 7
        return currDay
    
    def getISIN(self, day: date):
        currDay = day
        worksheet = None
        while worksheet is None:
            worksheet = self.getWorksheet(currDay)
            currDay -= datetime.timedelta(days=1)
        # isin col index: 2
        return self.extractColumn( worksheet, 2 )
    
    # ==========================================================================
    
    def extractColumn(self, worksheet, colIndex):
        # name col: 1
        # rows are indexed by 0, first row is header 
        ret = dict()
        for row in range(1, worksheet.nrows):
            name = worksheet.cell(row, 1).value
            value = worksheet.cell(row, colIndex).value
            ret[ name ] = value
        return ret
    
    def getWorksheet(self, day: date):
        _LOGGER.debug( "getting data from date: %s", day )
        dataFile = self.crawler.getStockData( day )
        
        try:
            workbook = xlrd.open_workbook( dataFile )
            worksheet = workbook.sheet_by_index(0)
            return worksheet
        except xlrd.biffh.XLRDError as err:
            message = str(err)
            if "Unsupported format" not in message:
                _LOGGER.exception( "Error" )
                return None

            # Unsupported format
            if self.isFileWithNoData(dataFile) is False:
                _LOGGER.exception( "Error" )
                return None
                
            # Brak danych dla wybranych kryteriów.
            _LOGGER.info("day without stock: %s", day )
            return None
        return None
    
    def isFileWithNoData(self, filePath):
        with open( filePath ) as f:
            if "Brak danych dla wybranych kryteriów." in f.read():
                return True
        return False
