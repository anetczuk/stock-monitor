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
# import datetime

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import qApp

from stockmonitor.gui.appwindow import AppWindow
from stockmonitor.gui.widget import logwidget
from stockmonitor.gui.widget.dataframetable import DataFrameTable
from stockmonitor.gui.trayicon import load_main_icon, load_chart_icon
from stockmonitor.gui.utils import set_label_url

from . import uiloader
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

        self.refreshAction = QtWidgets.QAction(self)
        self.refreshAction.setShortcuts( QtGui.QKeySequence.Refresh )
        self.refreshAction.triggered.connect( self.refreshStockDataForce )
        self.addAction( self.refreshAction )

        self.ui.walletValueLabel.setStyleSheet("font-weight: bold")
        self.ui.walletProfitLabel.setStyleSheet("font-weight: bold")
        self.ui.overallProfitLabel.setStyleSheet("font-weight: bold")

        self.tickTimer = QtCore.QTimer( self )
        self.tickTimer.timeout.connect( self.updateTrayIndicator )
        self.tickTimer.start( 60 * 1000 )                           ## every minute

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
        self.ui.actionLogs.triggered.connect( self.openLogsWindow )
        self.ui.actionOptions.triggered.connect( self.openSettingsDialog )

        ## =============================================================

        self.trayIcon = trayicon.TrayIcon(self)
        self._setIconTheme( trayicon.TrayIconTheme.WHITE )

        self.ui.activitywidget.connectData( self.data )
        self.ui.daywidget.connectData( self.data )

        self.ui.espiList.connectData( self.data )

        self.ui.gpwIndexesTable.connectData( self.data )

        self.ui.stockFullTable.connectData( self.data )
        self.ui.favsWidget.connectData( self.data )
        self.ui.walletwidget.connectData( self.data )
        self.ui.transactionswidget.connectData( self.data )

        self.ui.indicatorswidget.connectData( self.data )
        self.ui.reportswidget.connectData( self.data )
        self.ui.recentrepswidget.connectData( self.data )
        self.ui.dividendswidget.connectData( self.data )

        self.ui.gpwIndexesSourceLabel.setOpenExternalLinks(True)
        indexesDataAccess = self.data.gpwIndexesData
        set_label_url( self.ui.gpwIndexesSourceLabel, indexesDataAccess.sourceLink() )

        self.ui.globalIndexesSourceLabel.setOpenExternalLinks(True)
        indexesDataAccess = self.data.globalIndexesData
        set_label_url( self.ui.globalIndexesSourceLabel, indexesDataAccess.sourceLink() )

        self.ui.espiSourceLabel.setOpenExternalLinks(True)
        set_label_url( self.ui.espiSourceLabel, self.data.gpwESPIData.sourceLink() )

        self.ui.stockSourceLabel.setOpenExternalLinks(True)
        set_label_url( self.ui.stockSourceLabel, self.data.gpwCurrentSource.stockData.sourceLink() )

        ## ================== connecting signals ==================

        self.data.favsChanged.connect( self._handleFavsChange )
        self.data.stockDataChanged.connect( self._updateStockViews )
        self.data.stockDataChanged.connect( self._updateWalletSummary )
        self.data.walletDataChanged.connect( self._updateWalletSummary )
        self.data.stockHeadersChanged.connect( self._handleStockHeadersChange )

        self.ui.favsWidget.addFavGrp.connect( self.data.addFavGroup )
        self.ui.favsWidget.renameFavGrp.connect( self.data.renameFavGroup )
        self.ui.favsWidget.removeFavGrp.connect( self.data.deleteFavGroup )
        self.ui.favsWidget.favsChanged.connect( self.triggerSaveTimer )

        self.ui.stockRefreshPB.clicked.connect( self.refreshStockDataForce )

        self.ui.notesWidget.dataChanged.connect( self._handleNotesChange )

        #qApp.saveStateRequest.connect( self.saveSession )
        #qApp.aboutToQuit.connect( self.saveOnQuit )

#         self.applySettings()
        self.trayIcon.show()

        self.setWindowTitle()

        self.setStatusMessage( "Ready", timeout=10000 )

    def loadData(self):
        """Load user related data (e.g. favs, notes)."""
        dataPath = self.getDataPath()
        self.data.load( dataPath )
        self.data.loadDownloadedStocks()
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
        if hasattr(self, 'trayIcon'):
            self.trayIcon.setToolTip( newTitle )

    def refreshView(self):
        self._updateStockViews()
        self._updateWalletSummary()
        self.ui.stockFullTable.updateData()
        self.ui.stockFullTable.updateView()
        self.ui.walletwidget.updateView()
        self.ui.transactionswidget.updateView()
        self.ui.favsWidget.updateView()
        self.ui.notesWidget.setNotes( self.data.notes )

    def refreshStockDataForce(self):
        self.refreshAction.setEnabled( False )
        self.ui.stockRefreshPB.setEnabled( False )
        self.data.refreshStockData( True )

    def _updateStockViews(self):
        _LOGGER.info( "handling stock change" )
        self._updateStockTimestamp()

        self.ui.espiList.updateView()

        self._updateGpwIndexes()

        data = self.data.globalIndexesData.getWorksheet()
        self.ui.globalIndexesTable.setData( data )

        self.ui.indicatorswidget.refreshData()
        self.ui.reportswidget.refreshData()
        self.ui.recentrepswidget.refreshData()
        self.ui.dividendswidget.refreshData()

        self.refreshAction.setEnabled( True )
        self.ui.stockRefreshPB.setEnabled( True )

        self.setStatusMessage( "Stock data refreshed" )

    def _updateGpwIndexes(self):
        data = self.data.gpwIndexesData.getWorksheet()
        self.ui.gpwIndexesTable.setData( data )

    def _updateWalletSummary(self):
#         self.ui.walletValueLabel.setText( "None" )
#         self.ui.walletProfitLabel.setText( "None" )
#         self.ui.overallProfitLabel.setText( "None" )

        profit = self.data.getWalletState()
        walletValue   = profit[0]
        walletProfit  = profit[1]
        overallProfit = profit[2]
        self.ui.walletValueLabel.setText( str(walletValue) )
        self.ui.walletProfitLabel.setText( str(walletProfit) )
        self.ui.overallProfitLabel.setText( str(overallProfit) )

    def _handleStockHeadersChange(self):
        self.triggerSaveTimer()
        self.setStatusMessage( "Stock headers changed" )

    def _updateStockTimestamp(self):
        ## update stock timestamp
        timestamp = self.data.gpwCurrentData.grabTimestamp
        if timestamp is None:
            self.ui.refreshTimeLabel.setText("None")
        else:
            dateString = timestamp.strftime( "%Y-%m-%d %H:%M:%S" )
            self.ui.refreshTimeLabel.setText( dateString )

    def _handleFavsChange(self):
        self.triggerSaveTimer()

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
        self._setIconTheme( theme )
        self.updateTrayIndicator()

    def _setIconTheme(self, theme: trayicon.TrayIconTheme):
        appIcon = load_main_icon( theme )
        self.setWindowIcon( appIcon )
        self.trayIcon.setIcon( appIcon )

        ## update charts icon
        chartIcon = load_chart_icon( theme )
        widgets = self.findChildren( AppWindow )
        for w in widgets:
            w.setWindowIcon( chartIcon )
    
    def updateTrayIndicator(self):
        self.data.gpwIndexesData.refreshData()
        isin = "PL9999999987"                                               ## wig20
        recentChange = self.data.gpwIndexesData.getRecentChange( isin )
        indicateColor = None
        if recentChange < 0:
            indicateColor = QtGui.QColor(255, 96, 32)
        else:
            indicateColor = QtGui.QColor("lime")
        absVal = abs( recentChange )
        value = str( absVal )
#         if absVal < 1.0:
#             value = value[1:]
        self.trayIcon.drawStringAuto( value, indicateColor )
        self._updateGpwIndexes()

    def getIconTheme(self) -> trayicon.TrayIconTheme:
        return self.appSettings.trayIcon

    # Override closeEvent, to intercept the window closing event
    def closeEvent(self, event):
        _LOGGER.info("received close event, saving session: %s", qApp.isSavingSession() )
        if qApp.isSavingSession():
            ## closing application due to system shutdown
            self.saveAll()
            return
        ## windows close requested by user -- hide the window
        event.ignore()
        self.hide()
        self.trayIcon.show()

    def showEvent(self, _):
        self.trayIcon.updateLabel()

    def hideEvent(self, _):
        self.trayIcon.updateLabel()

    def setVisible(self, state):
        childrenWindows = self.findChildren( AppWindow )
        for w in childrenWindows:
            w.setVisible( state )
        super().setVisible( state )

    ## ====================================================================

    # pylint: disable=R0201
    def closeApplication(self):
        _LOGGER.info("received close request")
        ##self.close()
        qApp.quit()

    def saveAll(self):
        _LOGGER.info("saving application state")
        self.saveSettings()
        self.saveData()

    ## ====================================================================

    def openLogsWindow(self):
        logwidget.create_window( self )

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
        """Load Qt related settings (e.g. layouts, sizes)."""
        settings = self.getSettings()
        self.logger.debug( "loading app state from %s", settings.fileName() )

        self.appSettings.loadSettings( settings )
        self.ui.stockFullTable.loadSettings( settings )
        self.ui.favsWidget.loadSettings( settings )

        widgets = self.findChildren( DataFrameTable )
        widgetsList = guistate.sort_widgets( widgets )
        for w, _ in widgetsList:
            w.loadSettings( settings )

        self.applySettings()

        ## restore widget state and geometry
        guistate.load_state( self, settings )

    def saveSettings(self):
        settings = self.getSettings()
        self.logger.debug( "saving app state to %s", settings.fileName() )

        self.appSettings.saveSettings( settings )
        self.ui.stockFullTable.saveSettings( settings )
        self.ui.favsWidget.saveSettings( settings )

        widgets = self.findChildren( DataFrameTable )
        widgetsList = guistate.sort_widgets( widgets )
        for w, _ in widgetsList:
            w.saveSettings( settings )

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
