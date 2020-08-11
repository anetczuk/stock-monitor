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

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import qApp
from PyQt5.QtGui import QIcon

from . import uiloader
from . import resources
from . import trayicon
from . import guistate
from .dataobject import DataObject

from .widget.settingsdialog import SettingsDialog, AppSettings


_LOGGER = logging.getLogger(__name__)


UiTargetClass, QtBaseClass = uiloader.load_ui_from_module_path( __file__ )


class MainWindow( QtBaseClass ):           # type: ignore

    logger: logging.Logger = None
    appTitle = "Stock Monitor"

    def __init__(self):
        super().__init__()
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.data = DataObject( self )
        self.appSettings = AppSettings()

        self.setWindowTitle( self.appTitle )
        
        refreshAction = QtWidgets.QAction(self)
        refreshAction.setShortcuts( QtGui.QKeySequence.Refresh )
        refreshAction.triggered.connect( self.data.refreshStockData )
        self.addAction( refreshAction )

        ## =============================================================

        undoStack = self.data.undoStack

        undoAction = undoStack.createUndoAction( self, "&Undo" )
        undoAction.setShortcuts( QtGui.QKeySequence.Undo )
        redoAction = undoStack.createRedoAction( self, "&Redo" )
        redoAction.setShortcuts( QtGui.QKeySequence.Redo )

        self.ui.menuEdit.insertAction( self.ui.actionUndo, undoAction )
        self.ui.menuEdit.removeAction( self.ui.actionUndo )
        self.ui.menuEdit.insertAction( self.ui.actionRedo, redoAction )
        self.ui.menuEdit.removeAction( self.ui.actionRedo )
        
        self.ui.actionSave_data.triggered.connect( self.saveData )
        self.ui.actionOptions.triggered.connect( self.openSettingsDialog )

        ## =============================================================

        self.trayIcon = trayicon.TrayIcon(self)
        self.trayIcon.setToolTip( self.appTitle )
        self._updateIconTheme( trayicon.TrayIconTheme.WHITE )

        self.ui.stockFullTable.connectData( self.data )
        self.ui.favsWidget.connectData( self.data )

        ## === connecting signals ===

        self.data.favsChanged.connect( self._handleFavsChange )
        self.data.stockDataChanged.connect( self._handleStockDataChange )

        self.ui.favsWidget.addFavGrp.connect( self.data.addFavGroup )
        self.ui.favsWidget.renameFavGrp.connect( self.data.renameFavGroup )
        self.ui.favsWidget.removeFavGrp.connect( self.data.deleteFavGroup )
        self.ui.favsWidget.favsChanged.connect( self.triggerSaveTimer )

        self.ui.stockRefreshPB.clicked.connect( self.data.refreshStockData )

        self.ui.notesWidget.dataChanged.connect( self._handleNotesChange )

        self.applySettings()
        self.trayIcon.show()

        self.setStatusMessage( "Ready", timeout=10000 )

    def loadData(self):
        dataPath = self.getDataPath()
        self.data.load( dataPath )
        self.refreshView()

    def triggerSaveTimer(self):
        timeout = 30000
        _LOGGER.info("triggering save timer with timeout %s", timeout)
        QtCore.QTimer.singleShot( timeout, self.saveData )

    def saveData(self):
        if self._saveData():
            self.setStatusMessage( "Data saved" )
        else:
            self.setStatusMessage( "Nothing to save" )

    # pylint: disable=E0202
    def _saveData(self):
        ## having separate slot allows to monkey patch / mock "_saveData()" method
        _LOGGER.info( "storing data" )
        dataPath = self.getDataPath()
        self.data.notes = self.ui.notesWidget.getNotes()
        return self.data.store( dataPath )

    def disableSaving(self):
        def save_data_mock():
            _LOGGER.info("saving data is disabled")
        _LOGGER.info("disabling saving data")
        self._saveData = save_data_mock           # type: ignore

    def getDataPath(self):
        settings = self.getSettings()
        settingsDir = settings.fileName()
        settingsDir = settingsDir[0:-4]       ## remove extension
        settingsDir += "-data"
        return settingsDir

    ## ====================================================================

    def refreshView(self):
        self._updateStockTimestamp()
        self.updateFavsView()
        self.ui.notesWidget.setNotes( self.data.notes )

    def _handleStockDataChange(self):
        self._updateStockTimestamp()
        self.setStatusMessage( "Stock data refreshed" )

    def _updateStockTimestamp(self):
        ## update stock timestamp
        timestamp = self.data.currentStockData.grabTimestamp
        if timestamp is None:
            self.ui.refreshTimeLabel.setText("None")
        else:
            dateString = timestamp.strftime( "%Y-%m-%d %H:%M:%S" )
            self.ui.refreshTimeLabel.setText( dateString )

    def _handleFavsChange(self):
        self.triggerSaveTimer()
#         self.updateFavsView()

    def updateFavsView(self):
        self.ui.favsWidget.updateView()

    ## ====================================================================

    def _handleNotesChange(self):
        self.triggerSaveTimer()

    ## ====================================================================

    def setStatusMessage(self, firstStatus, changeStatus: list=None, timeout=6000):
        if not changeStatus:
            changeStatus = [ firstStatus + " +", firstStatus + " =" ]
        statusBar = self.statusBar()
        message = statusBar.currentMessage()
        if message == firstStatus:
            statusBar.showMessage( changeStatus[0], timeout )
            return
        try:
            currIndex = changeStatus.index( message )
            nextIndex = ( currIndex + 1 ) % len(changeStatus)
            statusBar.showMessage( changeStatus[nextIndex], timeout )
        except ValueError:
            statusBar.showMessage( firstStatus, timeout )

    def setIconTheme(self, theme: trayicon.TrayIconTheme):
        _LOGGER.debug("setting tray theme: %r", theme)
        self._setTrayIndicator( theme )

    def _setTrayIndicator(self, theme: trayicon.TrayIconTheme):
        self._updateIconTheme( theme )

    def _updateIconTheme(self, theme: trayicon.TrayIconTheme):
        fileName = theme.value
        iconPath = resources.get_image_path( fileName )
        appIcon = QIcon( iconPath )

        self.setWindowIcon( appIcon )
        self.trayIcon.setIcon( appIcon )

    # Override closeEvent, to intercept the window closing event
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.trayIcon.show()

    def showEvent(self, _):
        self.trayIcon.updateLabel()

    def hideEvent(self, _):
        self.trayIcon.updateLabel()

    ## ====================================================================

    # pylint: disable=R0201
    def closeApplication(self):
        ##self.close()
        qApp.quit()

    ## ====================================================================

    def openSettingsDialog(self):
        dialog = SettingsDialog( self.appSettings, self )
        dialog.setModal( True )
        dialog.iconThemeChanged.connect( self.setIconTheme )
        dialogCode = dialog.exec_()
        if dialogCode == QDialog.Rejected:
            self.applySettings()
            return
        self.appSettings = dialog.appSettings
        self.applySettings()

    def applySettings(self):
        self.setIconTheme( self.appSettings.trayIcon )

    def loadSettings(self):
        settings = self.getSettings()
        self.logger.debug( "loading app state from %s", settings.fileName() )

        self.appSettings.loadSettings( settings )
        self.ui.stockFullTable.loadSettings( settings )
        self.ui.favsWidget.loadSettings( settings )

        self.applySettings()

        ## restore widget state and geometry
        guistate.load_state( self, settings )

    def saveSettings(self):
        settings = self.getSettings()
        self.logger.debug( "saving app state to %s", settings.fileName() )

        self.appSettings.saveSettings( settings )
        self.ui.stockFullTable.saveSettings( settings )
        self.ui.favsWidget.saveSettings( settings )

        ## store widget state and geometry
        guistate.save_state(self, settings)

        ## force save to file
        settings.sync()

    def getSettings(self):
        ## store in home directory
        orgName = qApp.organizationName()
        appName = qApp.applicationName()
        settings = QtCore.QSettings(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, orgName, appName, self)
        return settings


MainWindow.logger = _LOGGER.getChild(MainWindow.__name__)
