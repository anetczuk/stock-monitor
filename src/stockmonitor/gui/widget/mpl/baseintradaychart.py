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


class BaseIntradayChart( MplCanvas ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget, 10, 10, 80)

        self.mouseIndicators = dict()
        self.figure.canvas.mpl_connect('motion_notify_event', self._onPlotUpdateMouseIndicators )
        self.figure.canvas.mpl_connect('figure_leave_event', self._onPlotHideMouseIndicators )

    def clearPlot(self):
#         if self.figure.get_visible() is True:
#             self.figure.set_visible( False )

        allaxes = self.figure.get_axes()
        for ax in allaxes:
            ax.cla()

    def _onPlotUpdateMouseIndicators( self, event ):
        plot = event.inaxes
        if plot is None:
            self._removeMouseIndicators()
            return
        if len(plot.lines) < 1:
            self._removeMouseIndicators()
            return
        if event.xdata is None:
            self._removeMouseIndicators()
            return

        self._removeMouseIndicators( plot )

        firstLine = plot.lines[0]
        xdata = firstLine.get_xdata()
        ydata = firstLine.get_ydata()
        xindex = get_index_float( xdata, event.xdata )
        yvalue = ydata[ xindex ]

        indicators = self.mouseIndicators.get( event.inaxes, None )
        if indicators is None:
            indicators = [ event.inaxes.axhline( y=yvalue, color="y", linestyle="--" ),
                           event.inaxes.axvline( x=event.xdata, color="y", linestyle="--" ) ]
            self.mouseIndicators[ event.inaxes ] = indicators
        else:
            indicators[0].set_data( [0, 1], [yvalue, yvalue] )
            indicators[1].set_data( [event.xdata, event.xdata], [0, 1] )

        self.draw_idle()

    def _onPlotHideMouseIndicators( self, _ ):
#     def _onPlotHideMouseIndicators( self, event ):
        self._removeMouseIndicators()

    def _removeMouseIndicators(self, preserve=None):
        keysList = set( self.mouseIndicators.keys() )
        for key in keysList:
            if key == preserve:
                continue
            lineList = self.mouseIndicators[ key ]
            for line in lineList:
                line.remove()
            del self.mouseIndicators[ key ]
        self.draw_idle()


def _configure_plot( plot, ylabel ):
    plot.set_xlabel( 'Time', fontsize=14 )
    plot.set_ylabel( ylabel, fontsize=14 )

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


def get_index_float( xdata, xvalue ):
    xtimestamp = pandas.Timestamp( xvalue, unit='D' )
    dataSize = len( xdata )
    for i in range(0, dataSize):
        currData = xdata[ i ]
        if xtimestamp < currData:
            return i - 1
    return dataSize - 1
