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
import datetime

from stockdataaccess import persist
from stockdataaccess.dataaccess import TMP_DIR


_LOGGER = logging.getLogger(__name__)


# Calendar with days without GPW
class HolidayData():

    def __init__(self):
        picklePath = self._storageFile()
        holidays = persist.load_object_simple( picklePath, None, silent=True )
        if holidays is not None:
            self.holidaySet = holidays
        else:
            self.holidaySet = set()
        self.holidaySize = len( self.holidaySet )

    def __del__(self):
        if len( self.holidaySet ) <= self.holidaySize:
            return
        ## new holiday added -- persist state
        self.storeHolidays()

    def isHoliday(self, day_date: datetime.date ):
        if HolidayData.isWeekend(day_date):
            return True
        if day_date < datetime.date( year=1991, month=4, day=16 ):
            ## first day of stock
            return True
#         if day_date.year < 2022:
#             _LOGGER.warning( f"unhandled case -- missing data: {day_date}" )
#             return False
        if day_date.year > 2022:
            _LOGGER.warning( "unhandled case -- missing data: %s", day_date )
            return False
        return day_date in self.holidaySet

    def markHoliday( self, day_date: datetime.date ):
        self.holidaySet.add( day_date )
        if len( self.holidaySet ) - self.holidaySize > 50:
            ## new holiday added -- persist state
            self.storeHolidays()

    def storeHolidays(self):
        picklePath = self._storageFile()
        _LOGGER.debug( "storing holiday data to: %s", picklePath )
        persist.store_object_simple( self.holidaySet, picklePath )
        self.holidaySize = len( self.holidaySet )

    def _storageFile(self):
        return f"{TMP_DIR}data/gpw/holidays.pickle"

    @staticmethod
    def isWeekend( day_date: datetime.date ):
        dayOfWeek = day_date.weekday()
        if dayOfWeek > 4:
            return True
        return False


def is_stock_holiday( day_date: datetime.date ):
    holidayCalendar = HolidayData()
    return holidayCalendar.isHoliday( day_date )
