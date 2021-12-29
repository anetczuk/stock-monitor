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

from enum import Enum, unique


@unique
class DataFieldType(Enum):
    TICKER = ()                  ## short code, e.g. 11B or CDR
    ISIN = ()                    ## ISIN, e.g. PLCCC0000016
    STOCK_NAME = ()              ## short name, e.g. SANPL
    FULL_NAME = ()               ## full name, e.g. "CD Projekt SA"

    def __new__(cls):
        value = len(cls.__members__)  # note no + 1
        obj = object.__new__(cls)
        # pylint: disable=W0212
        obj._value_ = value
        return obj


@unique
class ArchiveDataType(Enum):
    DATE = ()             ## data
    NAME = ()             ## nazwa
    ISIN = ()             ## numer ISIN
    CURRENCY = ()         ## waluta
    OPENING = ()          ## kurs otwarcia
    MAX = ()              ## kurs maksymalny
    MIN = ()              ## kurs minimalny
    CLOSING = ()          ## kurs zamkniecia
    CHANGE = ()           ## zmiana kursu
    VOLUME = ()           ## wolumen
    TRANSACTIONS = ()     ## liczba transakcji
    TRADING = ()          ## obrót, val/1k

    def __new__(cls):
        value = len(cls.__members__)  # note no + 1
        obj = object.__new__(cls)
        # pylint: disable=W0212
        obj._value_ = value
        return obj


@unique
class StockDataType(Enum):
    FULL_NAME = ()          ## nazwa (e.g. 4Fun Media SA)
    STOCK_NAME = ()         ## nazwa (e.g. 4FUNMEDIA)
    ISIN = ()               ## numer ISIN (e.g. PL4FNMD00013)
    TICKER = ()             ## skrot (always 3 letters, e.g. 11B or ZRE)
    CURRENCY = ()           ## waluta
    RECENT_TRANS_TIME = ()  ## czas ostatniej transakcji
    REFERENCE = ()          ## kurs odniesienia
    TKO = ()                ## TKO
    OPENING = ()            ## kurs otwarcia
    MIN = ()                ## kurs minimalny
    MAX = ()                ## kurs maksymalny
    RECENT_TRANS = ()       ## kurs ostatniej transakcji
    CHANGE_TO_REF = ()      ## zmiana do kursu odniesienia (wyrazona w %)
    
    NO_DIV_DAY = ()         ## Notowanie bez dywidendy

#     CLOSING = ()            ## kurs zamkniecia
#     CHANGE = ()             ## zmiana kursu
#     VOLUME = ()             ## wolumen
#     TRANSACTIONS = ()       ## liczba transakcji
#     TRADING = ()            ## obrót, val/1k

    def __new__(cls):
        value = len(cls.__members__)  # note no + 1
        obj = object.__new__(cls)
        # pylint: disable=W0212
        obj._value_ = value
        return obj


@unique
class CompareDataType(Enum):
    VALUE = ()
    VOLUME = ()
    TRADING = ()
    TRANSACTIONS = ()

    def __new__(cls):
        value = len(cls.__members__)  # note no + 1
        obj = object.__new__(cls)
        # pylint: disable=W0212
        obj._value_ = value
        return obj
