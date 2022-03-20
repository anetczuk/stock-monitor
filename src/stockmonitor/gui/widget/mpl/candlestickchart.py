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

# from typing import List

import mplfinance as fplt

from stockmonitor.gui.widget.mpl.mplbasechart import get_index_float
from .mplbasechart import MplBaseChart
from .mplbasechart import _configure_plot


_LOGGER = logging.getLogger(__name__)


# CANDLE_TYPE = "ohlc"
CANDLE_TYPE  = "candle"

CANDLE_STYLE = "default"
# CANDLE_STYLE = "sas"
# CANDLE_STYLE = "yahoo"


class PriceCandleStickChart( MplBaseChart ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.xlabel = "Price"
        self.pricePlot  = self.figure.add_subplot(1, 1, 1)      ## matplotlib.axes._subplots.AxesSubplot

        self.clearPlot()

    def setXLabel(self, xLabel):
        self.xlabel = xLabel
        _configure_plot( self.pricePlot, self.xlabel )

    def clearPlot(self):
        super().clearPlot()

        _configure_plot( self.pricePlot, self.xlabel )

        # rotates and right aligns the x labels, and moves the bottom of the
        # axes up to make room for them
        self.figure.autofmt_xdate()

    def addPriceLine(self, xdata: List[datetime.datetime], ydata, color='r', style=None):
        line = self.pricePlot.plot_date( xdata, ydata, color, linewidth=2, antialiased=True )
        if style is not None:
            line[0].set_linestyle( style )

#         _update_plot( xdata, self.pricePlot )

        if self.figure.get_visible() is False:
            self.figure.set_visible( True )

        ## self.refreshCanvas()

    def addPriceHLine(self, yvalue, color='y', style="--"):
        self.pricePlot.axhline( y=yvalue, color=color, linestyle=style )

    def addPriceCandles(self, dataframe):
        _plot_data( dataframe, self.pricePlot, False )

        if self.figure.get_visible() is False:
            self.figure.set_visible( True )

#         self.refreshCanvas()

    def addPriceSecondaryY(self, referenceValue ):
        def val_to_perc( y ):
            return ( y / referenceValue - 1.0 ) * 100.0

        def perc_to_val( y ):
            return ( y / 100.0 + 1.0 ) * referenceValue

        secay = self.pricePlot.secondary_yaxis( 'right', functions=(val_to_perc, perc_to_val) )
        secay.set_ylabel( "Change [%]" )

        ## self.refreshCanvas()


class PriceValueCandleStickChart( MplBaseChart ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

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

    def addPriceLine(self, xdata: List[datetime.datetime], ydata, color='r', style=None):
        line = self.pricePlot.plot_date( xdata, ydata, color, linewidth=2, antialiased=True )
        if style is not None:
            line[0].set_linestyle( style )

#         _update_plot( xdata, self.pricePlot )

        if self.figure.get_visible() is False:
            self.figure.set_visible( True )

        ## self.refreshCanvas()

    def addPriceHLine(self, yvalue, color='y', style="--"):
        self.pricePlot.axhline( y=yvalue, color=color, linestyle=style )

    def addPricePoint( self, xdata: datetime.datetime, ydata, color='r', marker=".", markersize=12, annotation=None ):
        self.pricePlot.plot_date( xdata, ydata, color, marker=marker, markersize=markersize, antialiased=True )

        if annotation is not None:
            self.pricePlot.annotate( annotation, (xdata, ydata),
                                     textcoords="offset pixels", xytext=(1, 1), fontsize=16 )

        if self.figure.get_visible() is False:
            self.figure.set_visible( True )

#         self.refreshCanvas()

    def addPriceCandles(self, dataframe):
        _plot_data( dataframe, self.pricePlot, self.volumePlot )

        if self.figure.get_visible() is False:
            self.figure.set_visible( True )

        ## self.refreshCanvas()

    def addPriceSecondaryY(self, referenceValue ):
        def val_to_perc( y ):
            return ( y / referenceValue - 1.0 ) * 100.0

        def perc_to_val( y ):
            return ( y / 100.0 + 1.0 ) * referenceValue

        secay = self.pricePlot.secondary_yaxis( 'right', functions=(val_to_perc, perc_to_val) )
        secay.set_ylabel( "Change [%]" )

        ## self.refreshCanvas()

    def addVolumeSecondaryY(self, recentPrice ):
        def volume_to_value( vol ):
            return vol * recentPrice / 1000.0

        def value_to_volume( val ):
            return val / recentPrice * 1000.0

        secay = self.volumePlot.secondary_yaxis( 'right', functions=(volume_to_value, value_to_volume) )
        secay.set_ylabel( "Value [k]" )

        ## self.refreshCanvas()

    def _readCoords(self, event):
        plot = event.inaxes
        firstLine = plot.lines[0]
        xdata = firstLine.get_xdata()
        ydata = firstLine.get_ydata()
        xindex = get_index_float( xdata, event.xdata )
        yvalue = ydata[ xindex ]
        #print( "xxxxxx:", xdata, ydata, event.xdata, xindex, yvalue )
        return (event.xdata, yvalue)


def _plot_data( dataframe, pricePlot, volumePlot=False ):
    xdata = dataframe.index
    date_format = get_date_format( xdata )

#         mc    = fplt.make_marketcolors( up='green', down='red' )
#         style = fplt.make_mpf_style( base_mpf_style=CANDLE_STYLE, marketcolors=mc )

    avg_dist_between_points = (xdata[-1] - xdata[0]) / float(len(xdata))
    start_day = (xdata[0]  - 0.45 * avg_dist_between_points).timestamp() / (60 * 60 * 24)
    end_day   = (xdata[-1] + 0.45 * avg_dist_between_points).timestamp() / (60 * 60 * 24)

    fplt.plot( dataframe,
               type=CANDLE_TYPE,
               style=CANDLE_STYLE,
               ax=pricePlot,
               volume=volumePlot,
               datetime_format=date_format,
               show_nontrading=True,
               xlim=(start_day, end_day)
               )

#         _update_plot( xdata, volumePlot )


## set axis ticks formatting
# def _update_plot( xdata, plot ):
def _update_plot( _, plot ):
#     format = get_date_format( xdata )
#     formatter = matplotlib.dates.DateFormatter( format )
#     plot.xaxis.set_major_formatter( formatter )

    plot.relim(True)
    plot.autoscale_view()


def get_date_format( xdata ):
    if len(xdata) > 1:
        timeSpan = xdata[-1] - xdata[0]
        if timeSpan > datetime.timedelta( days=2 ):
            ## long format
            return '%d-%m-%Y'
    return '%H:%M:%S'


# def get_index_float( xdata, xvalue ):
#     dataSize = len( xdata )
#     if dataSize < 2:
#         return 0
# #     valueDate = matplotlib.dates.num2date( xvalue )
# #     valueDate = valueDate.replace( tzinfo=None )            ## remove timezone info
#     valueDate = xvalue
#     for i in range(0, dataSize):
#         currData = xdata[ i ]
#         if currData <= valueDate:
#             continue
#         nextDist = currData - valueDate
#         prevData = xdata[ i - 1 ]
#         prevDist = valueDate - prevData
#         if prevDist < nextDist:
#             return i - 1
#         return i
#     return dataSize - 1


def set_ref_format_coord( plot, refValue=None ):
    if len(plot.lines) < 1:
        return
    firstLine  = plot.lines[0]
    xdata      = firstLine.get_xdata()
    ydata      = firstLine.get_ydata()
    xformatter = plot.xaxis.get_major_formatter()

    def format_coord(x, _):
#         def format_coord(x, y):
        xindex = get_index_float( xdata, x )
        yvalue = ydata[ xindex ]
        if refValue is not None:
            xvalue = xformatter.format_data(x)
            change = ( yvalue / refValue - 1 ) * 100
            return f"x={xvalue} y={yvalue:.4f} ch={change:.2f}%"
        xvalue = xformatter.format_data(x)
        return f"x={xvalue} y={yvalue:.4f}"

    plot.format_coord = format_coord


def set_int_format_coord( plot ):
    if len(plot.lines) < 1:
        return
    firstLine  = plot.lines[0]
    xdata      = firstLine.get_xdata()
    ydata      = firstLine.get_ydata()
    xformatter = plot.xaxis.get_major_formatter()

    def format_coord(x, _):
#         def format_coord(x, y):
        xvalue = xformatter.format_data(x)
        xindex = get_index_float( xdata, x )
        yvalue = ydata[ xindex ]
        return f"x={xvalue} y={yvalue}"

    plot.format_coord = format_coord
