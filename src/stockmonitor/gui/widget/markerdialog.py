# MIT License
#
# Copyright (c) 2021 Arkadiusz Netczuk <dev.arnet@gmail.com>
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
import copy

from PyQt5 import QtWidgets, QtGui

from stockmonitor.datatypes.datatypes import MarkerEntry

from .. import uiloader


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


_LOGGER = logging.getLogger(__name__)


class MarkerDialog( QtBaseClass ):           # type: ignore

    def __init__(self, entry: MarkerEntry, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.entry: MarkerEntry = None

        for operation in MarkerEntry.OperationType:
            self.ui.operationCB.addItem( operation.name, operation )

        self.colorDialog = QtWidgets.QColorDialog( self )
        self.colorDialog.colorSelected.connect( self._pickerColorChanged )      #type: ignore

        self.ui.pickColorPB.clicked.connect( self._pickColor )

        self.ui.colorLE.textChanged.connect( self._colorTextChanged )

        self.finished.connect( self._done )

        self.setObject( entry )

    def setObject(self, entry: MarkerEntry):
        if entry is not None:
            self.entry = copy.deepcopy( entry )
        else:
            self.entry = MarkerEntry()

        if self.entry.ticker is not None:
            self.ui.tickerLE.setText( self.entry.ticker )
        if self.entry.operation is not None:
            index = self.entry.operation.value
            self.ui.operationCB.setCurrentIndex( index )
        if self.entry.value is not None:
            self.ui.valueSB.setValue( self.entry.value )
        if self.entry.amount is not None:
            self.ui.amountSP.setValue( self.entry.amount )

        self._displayColor( self.entry.color )

        if self.entry.notes is not None:
            self.ui.notesLE.setText( self.entry.notes )
        else:
            self.ui.notesLE.setText( self.entry.notes )

#         self.adjustSize()

    def _pickColor(self):
        self.colorDialog.exec_()                                ## modal mode
#         selectedColor = self.colorDialog.selectedColor()
#         if selectedColor.isValid():
#             colorName = selectedColor.name( QtGui.QColor.HexRgb )
#             self._displayColor( colorName )
#         else:
#             self._displayColor( self.entry.color )

    def _pickerColorChanged(self, newColor: QtGui.QColor ):
        colorText = newColor.name( QtGui.QColor.HexRgb )
        self._displayColor( colorText )

    def _colorTextChanged( self, newText: str ):
        self._displayColor( newText )

    def _displayColor( self, value: str ):
        if value is None:
            self.ui.colorLE.setText("")
            ## update color sample
            self.ui.colorSample.setStyleSheet( "" )
            return

        currColor = QtGui.QColor( value )
        self.colorDialog.setCurrentColor( currColor )
        self.ui.colorLE.setText( value )
        ## update color sample
        self.ui.colorSample.setStyleSheet( "background-color: %s;" % value )

    def _done(self, _):
        self.entry.ticker = self.ui.tickerLE.text()
        operation = self.ui.operationCB.currentData()
        self.entry.setOperation(operation)
        self.entry.value = self.ui.valueSB.value()
        self.entry.amount = self.ui.amountSP.value()
        colorText = self.ui.colorLE.text()
        if not colorText:
            ## empty string
            self.entry.color = None
        else:
            self.entry.color = colorText

        notesText = self.ui.notesLE.text()
        if notesText:
            self.entry.notes = notesText
        else:
            ## empty string
            self.entry.notes = None

#         selectedColor = self.colorDialog.selectedColor()
#         if selectedColor.isValid():
#             self.entry.color = selectedColor.name( QtGui.QColor.HexRgb )
