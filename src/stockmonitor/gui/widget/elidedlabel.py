##
## Code taken from: https://itqna.net/questions/14614/it-possible-use-elide-qlabel
##

import logging

from PyQt5 import QtCore, QtWidgets, QtGui


_LOGGER = logging.getLogger(__name__)


class ElidedLabel( QtWidgets.QLabel ):

    def __init__(self, parentWidget=None):
        super().__init__( parentWidget )

        self.defaultType = QtCore.Qt.ElideRight
        self.eliding     = False
        self.original    = ""
        self.urlLink     = None

    def setType(self, elideType):
        self.defaultType = elideType
        self.elide()

    def setText(self, text):
        self.original = text
        self.urlLink  = None
        super().setText(text)
        self.elide()

    def setUrl(self, url, text):
        self.original = text
        self.urlLink  = url
        super().setText(text)
        self.elide()

    def elide(self):
        if self.eliding is False:
            self.eliding = True

        metrics = QtGui.QFontMetrics( self.font() )
        newText = metrics.elidedText( self.original, self.defaultType, self.width() )
        if self.urlLink is not None:
            urlText = "<a href=\"{urlLink}\">{newText}</a>"
            super().setText( urlText )
        else:
            super().setText( newText )

        self.eliding = False

    def resizeEvent(self, _):
#     def resizeEvent(self, event):
        QtCore.QTimer.singleShot( 50, self.elide )
