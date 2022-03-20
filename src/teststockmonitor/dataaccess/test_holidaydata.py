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

from stockmonitor.dataaccess.holidaydata import HolidayData


class HolidayDataTest(unittest.TestCase):

    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_isHoliday_WeekDay(self):
        data = HolidayData()
        day = datetime.date( year=2022, month=3, day=11 )       ## 2022.03.11 -- Friday
        holiday = data.isHoliday( day )
        self.assertEqual( holiday, False )

    def test_isHoliday_EndOfWeek(self):
        data = HolidayData()
        day = datetime.date( year=2022, month=3, day=12 )       ## 2022.03.12 -- Saturday
        holiday = data.isHoliday( day )
        self.assertEqual( holiday, True )

    def test_isHoliday_holiday(self):
        data = HolidayData()
        day = datetime.date( year=2022, month=1, day=6 )
        holiday = data.isHoliday( day )
        self.assertEqual( holiday, True )
