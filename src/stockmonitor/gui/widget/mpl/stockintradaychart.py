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

from .baseintradaychart import BaseIntradayChart
from .baseintradaychart import _configure_plot, _update_plot, get_index_float


_LOGGER = logging.getLogger(__name__)


class StockIntradayChart( BaseIntradayChart ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.pricePlot  = self.figure.add_subplot(2, 1, 1)      ## matplotlib.axes._subplots.AxesSubplot
        self.volumePlot = self.figure.add_subplot(2, 1, 2)      ## matplotlib.axes._subplots.AxesSubplot
        self.clearPlot()

    def clearPlot(self):
        super().clearPlot()

        _configure_plot( self.pricePlot, "Price" )
        _configure_plot( self.volumePlot, "Volume" )

        # rotates and right aligns the x labels, and moves the bottom of the
        # axes up to make room for them
        self.figure.autofmt_xdate()

    def setPriceFormatCoord( self, xdata, ydata, refValue ):
        xformatter = self.pricePlot.xaxis.get_major_formatter()

        def format_coord(x, _):
#         def format_coord(x, y):
            xindex = get_index_float( xdata, x )
            yvalue = ydata[ xindex ]
            change = ( yvalue / refValue - 1 ) * 100
            return 'x=' + xformatter.format_data(x) + ' y=%1.4f ch=%1.2f%%' % ( yvalue, change )

        self.pricePlot.format_coord = format_coord

    def setVolumeFormatCoord( self, xdata, ydata ):
        xformatter = self.volumePlot.xaxis.get_major_formatter()

        def format_coord(x, _):
#         def format_coord(x, y):
            xindex = get_index_float( xdata, x )
            yvalue = ydata[ xindex ]
            return 'x=' + xformatter.format_data(x) + ' y=%i' % yvalue

        self.volumePlot.format_coord = format_coord

    def addPriceSecondaryY(self, yLabel, firstToSecondFunction, secondToFirstFunction):
        secay = self.pricePlot.secondary_yaxis( 'right', functions=(firstToSecondFunction, secondToFirstFunction) )
        if yLabel is not None:
            secay.set_ylabel( yLabel )

    def addPriceLine(self, xdata: List[datetime.datetime], ydata, color, style=None):
        line = self.pricePlot.plot_date( xdata, ydata, color, linewidth=2, antialiased=True )
        if style is not None:
            line[0].set_linestyle( style )

        _update_plot( xdata, self.pricePlot )

        if self.figure.get_visible() is False:
            self.figure.set_visible( True )

    def addVolumeLine(self, xdata: List[datetime.datetime], ydata, color, style=None):
        line = self.volumePlot.plot_date( xdata, ydata, color, linewidth=2, antialiased=True )
        if style is not None:
            line[0].set_linestyle( style )

        _update_plot( xdata, self.volumePlot )

        if self.figure.get_visible() is False:
            self.figure.set_visible( True )
