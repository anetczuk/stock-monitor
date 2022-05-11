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

from .mplbasechart import MplBaseChart
from .mplbasechart import _configure_plot, _update_plot, get_index_float


_LOGGER = logging.getLogger(__name__)


class PriceLineChart( MplBaseChart ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.ylabel = "Price"
        self.pricePlot  = self.figure.add_subplot(1, 1, 1)      ## matplotlib.axes._subplots.AxesSubplot
        self.clearPlot()

    def setXLabel(self, yLabel):
        self.ylabel = yLabel
        _configure_plot( self.pricePlot, xlabel="Time", ylabel=self.ylabel )

    def clearPlot(self):
        super().clearPlot()

        _configure_plot( self.pricePlot, xlabel="Time", ylabel=self.ylabel )

        # rotates and right aligns the x labels, and moves the bottom of the
        # axes up to make room for them
        self.figure.autofmt_xdate()

    def addPriceSecondaryY(self, referenceValue ):
        def val_to_perc( y ):
            return ( y / referenceValue - 1.0 ) * 100.0

        def perc_to_val( y ):
            return ( y / 100.0 + 1.0 ) * referenceValue

        secay = self.pricePlot.secondary_yaxis( 'right', functions=(val_to_perc, perc_to_val) )
        secay.set_ylabel( "Change [%]" )

    def addPriceLine(self, xdata: List[datetime.datetime], ydata, color='r', style=None):
        if len(xdata) < 1:
            _LOGGER.warning( "no data found" )
            return

        line = self.pricePlot.plot_date( xdata, ydata, color, linewidth=2, antialiased=True )
        if style is not None:
            line[0].set_linestyle( style )

        _update_plot( xdata, self.pricePlot )

        if self.figure.get_visible() is False:
            self.figure.set_visible( True )

        self.refreshCanvas()

    def addPricePoint( self, xdata: datetime.datetime, ydata, color='r', marker=".", markersize=12, annotation=None ):
        self.pricePlot.plot_date( xdata, ydata, color, marker=marker, markersize=markersize, antialiased=True )

        if annotation is not None:
            self.pricePlot.annotate( annotation, (xdata, ydata),
                                     textcoords="offset pixels", xytext=(1, 1), fontsize=16 )

        if self.figure.get_visible() is False:
            self.figure.set_visible( True )

        self.refreshCanvas()

    def addPriceHLine(self, yvalue, color='y', style="--"):
        self.pricePlot.axhline( y=yvalue, color=color, linestyle=style )


class PriceValueLineChart( MplBaseChart ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.pricePlot  = self.figure.add_subplot(2, 1, 1)      ## matplotlib.axes._subplots.AxesSubplot
        self.volumePlot = self.figure.add_subplot(2, 1, 2)      ## matplotlib.axes._subplots.AxesSubplot
        self.clearPlot()

    def clearPlot(self):
        super().clearPlot()

        _configure_plot( self.pricePlot, xlabel="Time", ylabel="Price" )
        _configure_plot( self.volumePlot, xlabel="Time", ylabel="Volume" )

        # rotates and right aligns the x labels, and moves the bottom of the
        # axes up to make room for them
        self.figure.autofmt_xdate()

    def setVolumeFormatCoord( self ):
        firstLine  = self.volumePlot.lines[0]
        xdata      = firstLine.get_xdata()
        ydata      = firstLine.get_ydata()
        xformatter = self.volumePlot.xaxis.get_major_formatter()

        def format_coord(x, _):
#         def format_coord(x, y):
            xindex = get_index_float( xdata, x )
            yvalue = ydata[ xindex ]
            return f"x={xformatter.format_data(x)} y={yvalue}"

        self.volumePlot.format_coord = format_coord

    def addPriceSecondaryY(self, referenceValue ):
        def val_to_perc( y ):
            return ( y / referenceValue - 1.0 ) * 100.0

        def perc_to_val( y ):
            return ( y / 100.0 + 1.0 ) * referenceValue

        secay = self.pricePlot.secondary_yaxis( 'right', functions=(val_to_perc, perc_to_val) )
        secay.set_ylabel( "Change [%]" )

    def addPriceLine(self, xdata: List[datetime.datetime], ydata, color='r', style=None):
        line = self.pricePlot.plot_date( xdata, ydata, color, linewidth=2, antialiased=True )
        if style is not None:
            line[0].set_linestyle( style )

        _update_plot( xdata, self.pricePlot )

        if self.figure.get_visible() is False:
            self.figure.set_visible( True )

        self.refreshCanvas()

    def addPricePoint( self, xdata: datetime.datetime, ydata, color='r', marker=".", markersize=12, annotation=None ):
        self.pricePlot.plot_date( xdata, ydata, color, marker=marker, markersize=markersize, antialiased=True )

        if annotation is not None:
            self.pricePlot.annotate( annotation, (xdata, ydata),
                                     textcoords="offset pixels", xytext=(1, 1), fontsize=16 )

        if self.figure.get_visible() is False:
            self.figure.set_visible( True )

        self.refreshCanvas()

    def addPriceHLine(self, yvalue, color='y', style="--"):
        self.pricePlot.axhline( y=yvalue, color=color, linestyle=style )

    def addVolumeSecondaryY(self, recentPrice ):
        def volume_to_value( vol ):
            return vol * recentPrice / 1000.0

        def value_to_volume( val ):
            return val / recentPrice * 1000.0

        secay = self.volumePlot.secondary_yaxis( 'right', functions=(volume_to_value, value_to_volume) )
        secay.set_ylabel( "Value [k]" )

        self.refreshCanvas()

    def addVolumeLine(self, xdata: List[datetime.datetime], ydata, color='b', style=None):
        line = self.volumePlot.plot_date( xdata, ydata, color, linewidth=2, antialiased=True )
        if style is not None:
            line[0].set_linestyle( style )

        _update_plot( xdata, self.volumePlot )

        if self.figure.get_visible() is False:
            self.figure.set_visible( True )

        self.refreshCanvas()
