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

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout

from stockmonitor.gui import trayicon
from stockmonitor.gui.trayicon import load_chart_icon


class AppWindow( QWidget ):

    appTitle = "Stock Monitor"

    def __init__(self, parent=None):
        super().__init__( parent )
        self.setWindowFlags( Qt.Window )
        self.setWindowTitle( self.appTitle )

        self.vlayout = QVBoxLayout()
#         vlayout.setContentsMargins( 0, 0, 0, 0 )
        self.setLayout( self.vlayout )

        from stockmonitor.gui.mainwindow import MainWindow
        parentWindow = find_parent( self, MainWindow )
        if parentWindow is not None:
            iconTheme: trayicon.TrayIconTheme = parentWindow.appSettings.trayIcon
            chartIcon = load_chart_icon( iconTheme )
            self.setWindowIcon( chartIcon )

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


def find_parent(widget: QObject, type ):
    if widget is None:
        return None
    widget = get_parent( widget )
    while widget is not None:
        if isinstance(widget, type):
            return widget
        widget = get_parent( widget )
    return None


def get_parent( widget: QObject ):
    if callable(widget.parent) is False:
        ## some objects has "parent" attribute instead of "parent" method
        ## e.g. matplotlib's NavigationToolbar
        return None
    return widget.parent()
