# # MIT License
# #
# # Copyright (c) 2020 Arkadiusz Netczuk <dev.arnet@gmail.com>
# #
# # Permission is hereby granted, free of charge, to any person obtaining a copy
# # of this software and associated documentation files (the "Software"), to deal
# # in the Software without restriction, including without limitation the rights
# # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# # copies of the Software, and to permit persons to whom the Software is
# # furnished to do so, subject to the following conditions:
# #
# # The above copyright notice and this permission notice shall be included in all
# # copies or substantial portions of the Software.
# #
# # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# # SOFTWARE.
# #
# 
# import logging
# 
# from ... import uiloader
# 
# from .mpltoolbar import NavigationToolbar
# 
# 
# _LOGGER = logging.getLogger(__name__)
# 
# 
# UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )
# 
# 
# class TimelineChartWidget(QtBaseClass):             # type: ignore
# 
#     def __init__(self, parentWidget=None):
#         super().__init__(parentWidget)
# 
#         self.ui = UiTargetClass()
#         self.ui.setupUi(self)
# 
#         if parentWidget is not None:
#             bgcolor = parentWidget.palette().color(parentWidget.backgroundRole())
#             self.ui.dataChart.setBackgroundByQColor( bgcolor )
# 
#         self.ui.enabledCB.setChecked( True )
#         self.ui.enabledCB.stateChanged.connect( self._toggleEnabled )
# 
#         self.toolbar = NavigationToolbar(self.ui.dataChart, self)
#         self.ui.toolbarLayout.addWidget( self.toolbar )
# 
#         self._refreshWidget()
# 
#     def setData(self, xdata, ydata):
#         self.ui.dataChart.setData( xdata, ydata )
#         self._refreshWidget()
# 
#     def _refreshWidget(self):
#         enabledChart = self.ui.enabledCB.isChecked()
#         self.toolbar.setEnabled( enabledChart )
#         self.ui.dataChart.setEnabled( enabledChart )
# 
#     def _toggleEnabled(self, _):
#         ## state: 0 -- unchecked
#         ## state: 2 -- checked
#         self._refreshWidget()
