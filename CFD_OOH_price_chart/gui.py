from __future__ import annotations
from typing import List, Optional, Tuple, Union, Dict, TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from timeseries.classes import TimeSeries, TimeSeriesContainer, TimeSeries
    from instruments.classes import InstrumentSpecs, InstrumentInfo, PriceInstrument, InstrumentContainer, InstrumentContainer
    from subplot_structure.classes import SubPlotStructure
    from exchanges.classes import ExchangeInfo
    from PySide6.QtWidgets import QWidget, QHBoxLayout
    
import sys
from PySide6 import QtCore, QtWidgets
import workers
import pyqtgraph as pg
import custom_qt_classes.custom_widgets as custom_widgets
import utils
from custom_qt_classes.plot_data_item import CustomPlotDataItem
from custom_qt_classes.subplot_item import SubplotItem
from custom_qt_classes.subplot_widget import SubplotWidget, BlankWidget
import numpy as np
from misc import themes
from datetime import datetime
import utils
from custom_qt_classes import menu

pg.setConfigOption('background', 'k')
pg.setConfigOption('foreground', 'w')


class Window(QtWidgets.QMainWindow):
    n_plot_update_signal = QtCore.Signal(int)
    resizeSignal = QtCore.Signal()
    plot_dims_map, plot_blank_map, idx_ij_map = utils.subplot_dimensions()

    def __init__(self,
                 subplot_widget_container: Dict[str, SubplotWidget]={},
                 window_title: str="",
                 ):
        super().__init__()
        self.window_title=None
        self._n_plots=0
        self._n_rows=0
        self._n_cols=0
        self.menu=None
        self.subplot_widget_container: Dict[float, SubplotWidget] = {}
        self.blank_subplot_widget_container: Dict[float, BlankWidget] = {}
        
        self._close_event_callbacks=[]
        self.window_title=window_title
        self.init_layout(subplot_widget_container)    
        self.setWindowTitle(window_title)
        

        
        
    def setWindowTitle(self, window_title):
        self.window_title = window_title
        super().setWindowTitle(window_title)

    def count_subplots(self):
        self.calculate_window_dims()
        return self._n_plots
    
    def reset_window(self):
        for idx in range(self.subplot_layout.count()-1, -1, -1):
            hbox_layout = self.subplot_layout.itemAt(idx)
            self.subplot_layout.removeItem(hbox_layout)
            del hbox_layout

    def init_layout(self, subplot_widget_container: Dict[str, SubplotWidget]):
        self.setCentralWidget(QtWidgets.QWidget())
        self.central_layout = QtWidgets.QVBoxLayout(self.centralWidget())
        self.menu = menu.WindowMenu(subplot_widget_container)
        self.central_layout.addWidget(self.menu)
        self.plot_outer_widget = QtWidgets.QWidget()
        self.central_layout.addWidget(self.plot_outer_widget)
        self.subplot_layout = QtWidgets.QVBoxLayout()       
        self.plot_outer_widget.setLayout(self.subplot_layout)
        self.subplot_layout.setContentsMargins(0, 0, 0, 0)
        
        for subplot_widget in subplot_widget_container.values():
            self.n_plot_update_signal.connect(subplot_widget.menu.subplot_num_changed)
            subplot_widget.menu.blockSignals(True)
            self.add_subplot_widget(subplot_widget)
            subplot_widget.menu.blockSignals(False)
            self.resizeSignal.connect(subplot_widget.getPlotItem().vb.main_window_resize)
            subplot_widget.getPlotItem().vb.blockSignals(False)
        self.calculate_window_dims()
        self.n_plot_update_signal.emit(self._n_plots)        
        self.resizeSignal.connect(self._set_layout_stretch_factors)
        
        self.restructure_subplots()
        
    def add_blank_subplots(self):
        self.calculate_window_dims()
        
        blanks_required = self.plot_blank_map[self._n_plots]
        if blanks_required > 0:
            horizontal_layout = self.subplot_layout.itemAt(self.subplot_layout.count()-1).layout()
            for _ in range(blanks_required):
                blank_subplot = BlankWidget()
                blank_subplot.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                horizontal_layout.addWidget(blank_subplot)   
                self.blank_subplot_widget_container[blank_subplot.title()] = blank_subplot
            self.restructure_subplots()
    
    def remove_blank_subplots(self):
        for key, blank_subplot in self.blank_subplot_widget_container.copy().items():
            for idx in range(self.subplot_layout.count()-1, -1, -1):
                hbox_layout = self.subplot_layout.itemAt(idx)
                hbox_layout.removeWidget(blank_subplot)
        self.blank_subplot_widget_container={}

    def calculate_window_dims(self):
        self._n_plots = len(self.subplot_widget_container) + len(self.blank_subplot_widget_container)
        self._n_rows, self._n_cols = self.plot_dims_map[self._n_plots]


    def add_subplot_widget(self, subplot_widget: SubplotWidget, add_to_plot_widget_container: bool=True):
        n_rows = self.subplot_layout.count()
        if self.subplot_layout.count() == 0:
            hbox_layout = QtWidgets.QHBoxLayout()
            self.subplot_layout.addLayout(hbox_layout)
            self.subplot_layout.setStretch(0, 1)
        else:
            hbox_layout = self.subplot_layout.itemAt(n_rows-1)
        
        n_cols = hbox_layout.count()
        if n_cols == self._n_cols and n_rows > 0:
            hbox_layout = QtWidgets.QHBoxLayout() 
            self.subplot_layout.insertLayout(n_rows, hbox_layout)
            hbox_layout.setStretch(n_cols, 1)
        hbox_layout.addWidget(subplot_widget)
        if add_to_plot_widget_container:
            self.subplot_widget_container[subplot_widget.title()]=subplot_widget
            self._connect_shared_vb_signals(subplot_widget)
            self.n_plot_update_signal.connect(subplot_widget.menu.subplot_num_changed)
        self.calculate_window_dims()
        self.resizeSignal.connect(subplot_widget.getPlotItem().vb.reset_view)
        self.n_plot_update_signal.emit(self._n_plots)
        

    def remove_subplot_widget(self, subplot_widget: SubplotWidget):
        del self.subplot_widget_container[subplot_widget.title()]
        if len(self.subplot_widget_container) == 0:
            return
        for idx in range(self.subplot_layout.count()-1, -1, -1):
            hbox_layout = self.subplot_layout.itemAt(idx)
            for jdx in range(hbox_layout.count()-1, -1, -1):
                widget = hbox_layout.itemAt(jdx).widget()
                if widget == subplot_widget:
                    hbox_layout.removeWidget(subplot_widget)
                    if hbox_layout.count() == 0:
                        self.subplot_layout.removeItem(hbox_layout)
        self.restructure_subplots()
        self.n_plot_update_signal.emit(self._n_plots)
        
    def restructure_subplots(self):
        for idx in range(self.subplot_layout.count()-1, -1, -1):
            hbox_layout = self.subplot_layout.itemAt(idx)
            self.subplot_layout.removeItem(hbox_layout)
        
        self.calculate_window_dims()
        
        dims = self.plot_dims_map[self._n_plots]
        plot_titles = list(self.subplot_widget_container.keys())
        count=0
        for idx in range(dims[0]):
            hbox_layout = QtWidgets.QHBoxLayout()
            self.subplot_layout.addLayout(hbox_layout)
            self.subplot_layout.setStretch(0, 1)
            for jdx in range(dims[1]):
                if count < len(plot_titles):
                    subplot_widget = self.subplot_widget_container[plot_titles[count]]
                else:
                    subplot_widget = BlankWidget()
                    subplot_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

                hbox_layout.addWidget(subplot_widget)
                count+=1
        self.resizeSignal.emit()    

    def _remove_vb_signals(self, subplot_widget: SubplotWidget):
        for other_plot_widget in self.subplot_widget_container.values():
            if other_plot_widget != subplot_widget:
                if not subplot_widget.blank and not other_plot_widget.blank:
                    try:
                        subplot_widget.getPlotItem().vb.toggle_crosshairs_signal.disconnect(other_plot_widget.getPlotItem().vb.toggle_crosshairs)
                    except:
                        pass
                    try:
                        other_plot_widget.getPlotItem().vb.toggle_crosshairs_signal.disconnect(subplot_widget.getPlotItem().vb.toggle_crosshairs)
                    except:
                        pass
                    
    def _connect_shared_vb_signals(self, subplot_widget: SubplotWidget):
        for other_plot_widget in self.subplot_widget_container.values():
            if not subplot_widget.blank and not other_plot_widget.blank:
                subplot_widget.getPlotItem().vb.toggle_crosshairs_signal.connect(other_plot_widget.getPlotItem().vb.toggle_crosshairs)
                other_plot_widget.getPlotItem().vb.toggle_crosshairs_signal.connect(subplot_widget.getPlotItem().vb.toggle_crosshairs)
            
    def _set_layout_stretch_factors(self, *args):
        for i in range(self.subplot_layout.count()):
            self.subplot_layout.setStretch(i, 1)
            
        for i in range(self.subplot_layout.count()):
            hbox = self.subplot_layout.itemAt(i).layout()
            if hbox:
                for j in range(hbox.count()):
                    hbox.setStretch(j, 1)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resizeSignal.emit()
        
    def setWindowTitle(self, arg):
        for subplot_widget in self.subplot_widget_container.values():  
            if not subplot_widget.blank:
                subplot_widget.getPlotItem().vb.menu.set_window_title(arg)
            
        return super().setWindowTitle(arg)
    
    def add_close_event_callbacks(self, callback):
        self._close_event_callbacks.append(callback)
    
    def closeEvent(self, event):
        for callback in self._close_event_callbacks:
            callback(self)
            
    def showMaximized(self, *args, **kwargs):
        super().showMaximized(*args, **kwargs)
        

    