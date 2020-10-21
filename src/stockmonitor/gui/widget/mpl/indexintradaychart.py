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

from .baseintradaychart import BaseIntradayChart
from .baseintradaychart import _configure_plot, _update_plot


_LOGGER = logging.getLogger(__name__)


class IndexIntradayChart( BaseIntradayChart ):

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.pricePlot = self.figure.add_subplot(1, 1, 1)
        self.clearPlot()

    def clearPlot(self):
        super().clearPlot()

        _configure_plot( self.pricePlot, "Price" )

        # rotates and right aligns the x labels, and moves the bottom of the
        # axes up to make room for them
        self.figure.autofmt_xdate()

    def addPriceSecondaryY( self, referenceValue ):
        def val_to_perc( y ):
            return ( y / referenceValue - 1.0 ) * 100.0

        def perc_to_val( y ):
            return ( y / 100.0 + 1.0 ) * referenceValue

        secay = self.pricePlot.secondary_yaxis( 'right', functions=(val_to_perc, perc_to_val) )
        secay.set_ylabel( "Change [%]" )

    def addPriceLine(self, xdata, ydata, color='r', style=None):
        line = self.pricePlot.plot_date( xdata, ydata, color, linewidth=2, antialiased=True )
        if style is not None:
            line[0].set_linestyle( style )

        _update_plot( xdata, self.pricePlot )

        if self.figure.get_visible() is False:
            self.figure.set_visible( True )

        self.refreshCanvas()
