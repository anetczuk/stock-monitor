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

import pandas

from .mplcanvas import matplotlib, MplCanvas


_LOGGER = logging.getLogger(__name__)


class IndexIntradayChart( MplCanvas ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget, 10, 10, 80)

        self.pricePlot  = self.figure.add_subplot(1, 1, 1)
        self.clearPlot()

    def clearPlot(self):
#         if self.figure.get_visible() is True:
#             self.figure.set_visible( False )

        self.pricePlot.cla()
        
        self._configurePlot( self.pricePlot, "Price" )

        # rotates and right aligns the x labels, and moves the bottom of the
        # axes up to make room for them
        self.figure.autofmt_xdate()

    def addPriceSecondaryY(self, yLabel, firstToSecondFunction, secondToFirstFunction):
        secay = self.pricePlot.secondary_yaxis( 'right', functions=(firstToSecondFunction, secondToFirstFunction) )
        if yLabel is not None:
            secay.set_ylabel( yLabel )

    def addPriceLine(self, xdata, ydata, color, style=None):
        line = self.pricePlot.plot_date( xdata, ydata, color, linewidth=2, antialiased=True )
        if style is not None:
            line[0].set_linestyle( style )

        _update_plot( xdata, self.pricePlot )

        if self.figure.get_visible() is False:
            self.figure.set_visible( True )

    def _configurePlot(self, plot, ylabel):
        plot.set_xlabel( 'Time', fontsize=14 )
        plot.set_ylabel( ylabel, fontsize=14 )

        formatter = matplotlib.dates.DateFormatter('%H:%M:%S')
        plot.xaxis.set_major_formatter( formatter )
#         plot.xaxis_date()

        plot.margins( y=0.2 )
        plot.set_xmargin(0.0)      ## prevents empty space between first tick and y axis


def _update_plot(xdata, plot ):
    ticks = _generate_ticks(xdata, 12)
    plot.set_xticks( ticks )

    setLongFormat = False
    if len(ticks) > 1:
        timeSpan = ticks[-1] - ticks[0]
        if timeSpan > datetime.timedelta( days=2 ):
            setLongFormat = True

    if setLongFormat is True:
        formatter = matplotlib.dates.DateFormatter('%d-%m-%Y')
        plot.xaxis.set_major_formatter( formatter )
    else:
        formatter = matplotlib.dates.DateFormatter('%H:%M:%S')
        plot.xaxis.set_major_formatter( formatter )

    ### hide first and last major tick (next to plot edges)
#     xticks = plot.xaxis.get_major_ticks()
#     xticks[0].label1.set_visible(False)
    ##xticks[-1].label1.set_visible(False)

    plot.relim(True)
    plot.autoscale_view()


def _generate_ticks(xdata, number):
    if number < 1:
        return list()
    start = xdata[0].timestamp()
    tzoffset = start - pandas.Timestamp( start, unit="s" ).timestamp()
    if number < 2:
        middle = (start + xdata[-1].timestamp()) / 2 + tzoffset
        ts = pandas.Timestamp( middle, unit="s" )
        ticks = [ts]
        return ticks
#         print("data:", self.xdata, type(self.xdata))
    delta = (xdata[-1].timestamp() - start) / (number - 1)
    ticks = list()
    ticks.append( xdata[0] )
    currTs = start + tzoffset
    for _ in range(1, number):
        currTs += delta
        ts = pandas.Timestamp( currTs, unit="s" )
        ticks.append( ts )
    return ticks
