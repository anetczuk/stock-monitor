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

import pandas

from .mplcanvas import matplotlib, MplCanvas


_LOGGER = logging.getLogger(__name__)


class IndexIntradayChart( MplCanvas ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget, 10, 10, 80)

        self.xdata = list()
        self.ydata = list()

        self.pricePlot  = self.fig.add_subplot(1, 1, 1)
        self._configurePlot( self.pricePlot, "Price" )

        # rotates and right aligns the x labels, and moves the bottom of the
        # axes up to make room for them
        self.fig.autofmt_xdate()

        self._setPlotData()

    def setData(self, timedata, pricedata):
        self.xdata  = timedata
        self.ydata = pricedata
        self._setPlotData()

    def clearData(self):
        self.xdata.clear()
        self.ydata.clear()
        self._setPlotData()

    def _setPlotData(self):
        if len(self.xdata) < 2:
            return

        self.pricePlot.plot_date( self.xdata, self.ydata, 'r',
                                  linewidth=2, antialiased=True)

        self._updatePlot( self.pricePlot )

        self.fig.tight_layout()                 ## make space for labels of axis
#         self.fig.subplots_adjust(top=0.82)      ## make space for suptitle

    def _generateTicks(self, number):
        if number < 1:
            return list()
        start = self.xdata[0].timestamp()
        tzoffset = start - pandas.Timestamp( start, unit="s" ).timestamp()
        if number < 2:
            middle = (start + self.xdata[-1].timestamp()) / 2 + tzoffset
            ts = pandas.Timestamp( middle, unit="s" )
            ticks = [ts]
            return ticks
#         print("data:", self.xdata, type(self.xdata))
        delta = (self.xdata[-1].timestamp() - start) / (number - 1)
        ticks = list()
        ticks.append( self.xdata[0] )
        currTs = start + tzoffset
        for _ in range(1, number):
            currTs += delta
            ts = pandas.Timestamp( currTs, unit="s" )
            ticks.append( ts )
        return ticks

    def _configurePlot(self, plot, ylabel):
        plot.set_xlabel( 'Time', fontsize=14 )
        plot.set_ylabel( ylabel, fontsize=14 )

        formatter = matplotlib.dates.DateFormatter('%H:%M:%S')
        plot.xaxis.set_major_formatter( formatter )

        plot.margins( y=0.2 )
        plot.set_xmargin(0.0)      ## prevents empty space between first tick and y axis

    def _updatePlot(self, plot ):
        ticks = self._generateTicks(12)
        plot.set_xticks( ticks )

        ### hide first and last major tick (next to plot edges)
        xticks = plot.xaxis.get_major_ticks()
        xticks[0].label1.set_visible(False)
        ##xticks[-1].label1.set_visible(False)

        plot.relim(True)
        plot.autoscale_view()
