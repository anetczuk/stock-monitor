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

from typing import List

import mplfinance as fplt

from .mplbasechart import MplBaseChart
from .mplbasechart import _configure_plot, _update_plot, get_index_float


_LOGGER = logging.getLogger(__name__)


class PriceCandleStickChart( MplBaseChart ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.xlabel = "Price"
        self.candlesPlot  = self.figure.add_subplot(1, 1, 1)      ## matplotlib.axes._subplots.AxesSubplot
        self.clearPlot()

    def setXLabel(self, xLabel):
        self.xlabel = xLabel
        _configure_plot( self.candlesPlot, self.xlabel )

    def clearPlot(self):
        super().clearPlot()

        _configure_plot( self.candlesPlot, self.xlabel )

        # rotates and right aligns the x labels, and moves the bottom of the
        # axes up to make room for them
        self.figure.autofmt_xdate()

    def addPriceCandles(self, dataframe):
        fplt.plot( dataframe,
                   type='candle',
                   ax = self.candlesPlot
        )
  
        if self.figure.get_visible() is False:
            self.figure.set_visible( True )
 
        self.refreshCanvas()


class PriceValueCandleStickChart( MplBaseChart ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

#         self.candlesPlot  = self.figure.add_subplot(2, 1, 1)      ## matplotlib.axes._subplots.AxesSubplot
        self.pricePlot  = self.figure.add_subplot(2, 1, 1)      ## matplotlib.axes._subplots.AxesSubplot
        self.volumePlot = self.figure.add_subplot(2, 1, 2)      ## matplotlib.axes._subplots.AxesSubplot
        self.clearPlot()

    def clearPlot(self):
        super().clearPlot()

        _configure_plot( self.pricePlot,  "Price" )
        _configure_plot( self.volumePlot, "Volume" )

        # rotates and right aligns the x labels, and moves the bottom of the
        # axes up to make room for them
        self.figure.autofmt_xdate()

    def addPriceCandles(self, dataframe):
        fplt.plot( dataframe,
                   type='candle',
                   ax = self.pricePlot,
                   volume = self.volumePlot
        )
  
        if self.figure.get_visible() is False:
            self.figure.set_visible( True )
 
        self.refreshCanvas()
