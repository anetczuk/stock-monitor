#
#
#

import sys
import logging

try:
    import matplotlib

    # Make sure that we are using QT5
    matplotlib.use('Qt5Agg')

    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
except ImportError:
    ### No module named <name>
    logging.exception("Exception while importing")
    sys.exit(1)

# from PyQt5 import QtCore
from PyQt5 import QtWidgets


_LOGGER = logging.getLogger(__name__)


class MplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super().__init__( Figure( figsize=(width, height), dpi=dpi ) )

        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    ## fix fitting figure to widget
    def setTightAuto( self, enable: bool = True ):
        self.figure.set_tight_layout( enable )              # type: ignore

    def setBackgroundByRGB(self, r, g, b):
        rgbColor = ( r / 255, g / 255, b / 255, 1.0 )
        self.figure.patch.set_facecolor( rgbColor )

    def setBackgroundByQColor(self, bgcolor):
        rgbColor = ( bgcolor.red() / 255, bgcolor.green() / 255, bgcolor.blue() / 255, 1.0 )
        self.figure.patch.set_facecolor( rgbColor )

    def showFigure(self, show):
        currVis = self.figure.get_visible()
        if currVis == show:
            return
        self.figure.set_visible(show)
        self.draw()                         ## QWidget draw

    def refreshCanvas(self, tight=True):
        if tight:
            self.figure.tight_layout()
        self.draw_idle()

#     ## fix fitting figure to widget
#     def resizeEvent(self, event):
#         super().resizeEvent( event )
#         self.figure.tight_layout()


## =======================================================================


# class DynamicMplCanvas( MplCanvas ):
#     """A canvas that updates itself every second with a new plot."""
#
#     logger = None
#
#     def __init__(self, *args, **kwargs):
#         MplCanvas.__init__(self, *args, **kwargs)
#         self.timer = QtCore.QTimer(self)
#         self.timer.timeout.connect(self._update)
#         self._setTimer(True)
#
#     def setEnabled(self, enabled):
#         super().setEnabled(enabled)
#         if enabled is True:
#             self._update()
#             self._setTimer(enabled)
#         else:
#             self._setTimer(enabled)
#             self.clearData()
#             self.drawFigure()
#
#     def clearData(self):
#         ## implement if needed
#         pass
#
#     def updateData(self):
#         ## implement if needed
#         return False
#
#     def drawFigure(self):
#         if self._hasData() is False:
#             ## no data - nothing to do
#             self.showFigure( False )
#             return
#         self.showFigure( True )
#
# #         self.figure.canvas.draw()
# #         self.figure.canvas.flush_events()
#
#         ##self.draw()                         ## QWidget draw
#         self.draw_idle()
#
#     def _update(self):
#         self.updateData()
#         self.drawFigure()
#
#     def _setTimer(self, enabled):
#         if enabled is True:
#             self.timer.start(1000)
#         else:
#             self.timer.stop()
#
#     def _hasData(self):
#         axes = self.figure.get_axes()
#         if len(axes) < 1:
#             return False
#         ax = axes[0]
#         lines = ax.get_lines()
# #         self.logger.info("data:\n%r", lines)
#         if len(lines) < 1:
#             return False
#         ll = lines[0]
#         xdata = ll.get_xdata()
#         if len(xdata) < 1:
#             return False
#         return True
