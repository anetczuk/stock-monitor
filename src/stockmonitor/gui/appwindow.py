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

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout

from stockmonitor.gui import trayicon
from stockmonitor.gui.trayicon import load_chart_icon
from stockmonitor.gui.utils import get_parent


class AppWindow( QWidget ):

    appTitle = "Stock Monitor"

    def __init__(self, parent=None):
        super().__init__( parent )
        self.setWindowFlags( Qt.Window )
        self.setWindowTitle( self.appTitle )
        self.setAttribute( Qt.WA_DeleteOnClose )

        self.vlayout = QVBoxLayout()
#         vlayout.setContentsMargins( 0, 0, 0, 0 )
        self.setLayout( self.vlayout )

        widget = get_parent( self )
        while widget is not None:
            if hasattr(widget, 'getIconTheme') is False:
                widget = get_parent( widget )
                continue
            iconTheme: trayicon.TrayIconTheme = widget.getIconTheme()
            chartIcon = load_chart_icon( iconTheme )
            self.setWindowIcon( chartIcon )
            break

        self.refreshAction = QtWidgets.QAction(self)
        self.refreshAction.setShortcuts( QtGui.QKeySequence.Refresh )
        self.addAction( self.refreshAction )

        self.cancelAction = QtWidgets.QAction(self)
        self.cancelAction.setShortcuts( QtGui.QKeySequence.Cancel )
        self.cancelAction.triggered.connect( self.close )
        self.addAction( self.cancelAction )

    def setWindowTitleSuffix( self, suffix="" ):
        if len(suffix) < 1:
            self.setWindowTitle( suffix )
            return
        newTitle = AppWindow.appTitle + " " + suffix
        self.setWindowTitle( newTitle )

    def setWindowTitle( self, newTitle="" ):
        if len(newTitle) < 1:
            newTitle = AppWindow.appTitle
        super().setWindowTitle( newTitle )

    def addWidget(self, widget):
        self.vlayout.addWidget( widget )
