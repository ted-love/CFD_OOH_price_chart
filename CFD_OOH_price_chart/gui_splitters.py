from __future__ import annotations
from typing import List, Optional, Tuple, Union, Dict, TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from timeseries.classes import TimeSeries, TimeSeriesContainer, TimeSeries
    from instruments.classes import InstrumentSpecs, InstrumentInfo, PriceInstrument, InstrumentContainer, InstrumentContainer
    from subplot_structure.classes import SubPlotStructure
    from exchanges.classes import ExchangeInfo
    
import sys
from PySide6 import QtCore, QtWidgets
import workers
import pyqtgraph as pg
import custom_qt_classes.custom_widgets as custom_widgets
import utils
from custom_qt_classes.plot_data_item import CustomPlotDataItem
from custom_qt_classes.subplot_item import SubplotItem
from custom_qt_classes.subplot_widget import SubplotWidget
import numpy as np
from misc import themes
    

pg.setConfigOption('background', 'k')
pg.setConfigOption('foreground', 'w')


class Window(QtWidgets.QMainWindow):
    n_plot_update_signal = QtCore.Signal(int)

    def __init__(self,
                 subplot_widget_container: Dict[str, SubplotWidget]={},
                 window_title: str="",
                 ):
        self.window_title=None
        super().__init__()
        self._close_event_callbacks=[]
        if len(subplot_widget_container) > 0:
            self.init_window(subplot_widget_container,
                            window_title
                            )
    def init_window(self,
                    subplot_widget_container: Dict[str, SubplotWidget],
                    window_title: str,
                    ):
        self.subplot_widget_container = subplot_widget_container
        self.instrument_plot_items_map: Dict[str, List[SubplotItem]] = {}
        
        self._n_plots=0
        self._n_rows=0
        self._n_cols=0
        self.init_layout()    
        print(f"init_window")
        print(f'window_title: {window_title}')
        self.setWindowTitle(window_title)
        
    def setWindowTitle(self, window_title):
        self.window_title = window_title
        super().setWindowTitle(window_title)

    def count_subplots(self):
        return self._n_plots

    def init_layout(self):
        self.setCentralWidget(QtWidgets.QWidget())
        self.central_layout = QtWidgets.QVBoxLayout(self.centralWidget())       
        
        self.central_layout.addLayout(QtWidgets.QHBoxLayout())
        
        self._n_plots, self._n_rows, self._n_cols = self._calculate_window_dims()
        
        for subplot_widget in self.subplot_widget_container.values():
            self.n_plot_update_signal.connect(subplot_widget.menu.subplot_num_changed)
            subplot_widget.menu.blockSignals(True)
            self.add_subplot_widget(subplot_widget)
            subplot_widget.menu.blockSignals(False)
        
        self.n_plot_update_signal.emit(self._n_plots)
        self.n_plot_update_signal.connect(self._set_layout_stretch_factors)
                
    def _calculate_window_dims(self):
        n_plots = len(self.subplot_widget_container)
        nrows = np.floor(np.sqrt(n_plots)).astype(int)
        ncols = np.ceil(np.sqrt(n_plots))
        return n_plots, nrows, ncols

    def add_subplot_widget(self, subplot_widget: SubplotWidget):
        n_rows = self.central_layout.count()
        if self.central_layout.count() == 0:
            hbox_layout = QtWidgets.QHBoxLayout()
            self.central_layout.addLayout(hbox_layout)
            self.central_layout.setStretch(n_rows-1, 1)
        else:
            hbox_layout = self.central_layout.itemAt(n_rows-1)
        
        n_cols = hbox_layout.count()
        if n_cols == self._n_cols:
            hbox_layout = QtWidgets.QHBoxLayout() 
            self.central_layout.addLayout(hbox_layout)
            hbox_layout.setStretch(n_cols, 1)
        
        hbox_layout.addWidget(subplot_widget)
        self._connect_shared_vb_signals(subplot_widget)

    def remove_subplot_widget(self, subplot_widget: SubplotWidget):
        del self.subplot_widget_container[subplot_widget.title()]
        hbox_layout = self.central_layout.itemAt(self.central_layout.count()-1)
        hbox_layout.removeWidget(subplot_widget)
        if hbox_layout.count() == 0:
            self.central_layout.removeItem(hbox_layout)
        
    #    self._remove_vb_signals(subplot_widget)
            
        self._restructure_subplots()
        self.n_plot_update_signal.emit(self._n_plots)

    def _restructure_subplots(self):
        for idx in range(self.central_layout.count()-1, -1, -1):
            hbox_layout = self.central_layout.itemAt(idx)
            self.central_layout.removeItem(hbox_layout)
            
        self._n_plots, self._n_rows, self._n_cols = self._calculate_window_dims()
        
        for plot_widget_other in self.subplot_widget_container.values():
            plot_widget_other.menu.blockSignals(True)
            self.add_subplot_widget(plot_widget_other)
            plot_widget_other.menu.blockSignals(False)
    
    def _remove_vb_signals(self, subplot_widget: SubplotWidget):
        for other_plot_widget in self.subplot_widget_container.values():
            if other_plot_widget != subplot_widget:
                subplot_widget.getPlotItem().vb.toggle_crosshairs_signal.disconnect(other_plot_widget.getPlotItem().vb.toggle_crosshairs)
                other_plot_widget.getPlotItem().vb.toggle_crosshairs_signal.disconnect(subplot_widget.getPlotItem().vb.toggle_crosshairs)

    def _connect_shared_vb_signals(self, subplot_widget: SubplotWidget):
      #  if not subplot_widget in self.subplot_widget_container.values():
            for other_plot_widget in self.subplot_widget_container.values():
                subplot_widget.getPlotItem().vb.toggle_crosshairs_signal.connect(other_plot_widget.getPlotItem().vb.toggle_crosshairs)
                other_plot_widget.getPlotItem().vb.toggle_crosshairs_signal.connect(subplot_widget.getPlotItem().vb.toggle_crosshairs)
            
    def _set_layout_stretch_factors(self, *args):
        for i in range(self.central_layout.count()):
            self.central_layout.setStretch(i, 1)
            
        for i in range(self.central_layout.count()):
            hbox = self.central_layout.itemAt(i).layout()
            if hbox:
                for j in range(hbox.count()):
                    hbox.setStretch(j, 1)
    
    def resizeEvent(self, event):
        self._set_layout_stretch_factors()
        super().resizeEvent(event)
        
    def setWindowTitle(self, arg):
        for subplot_widget in self.subplot_widget_container.values():  
            subplot_widget.getPlotItem().vb.menu.set_window_title(arg)
            
        return super().setWindowTitle(arg)
    
    def add_close_event_callbacks(self, callback):
        self._close_event_callbacks.append(callback)
    
    def closeEvent(self, event):
        for callback in self._close_event_callbacks:
            callback(self)
class Window(QtWidgets.QMainWindow):
    n_plot_update_signal = QtCore.Signal(int)

    def __init__(self,
                 subplot_widget_container: Dict[str, SubplotWidget] = {},
                 window_title: str = "",
                 ):
        self.window_title = None
        super().__init__()
        self._close_event_callbacks = []
        if len(subplot_widget_container) > 0:
            self.init_window(subplot_widget_container, window_title)

    def init_window(self,
                    subplot_widget_container: Dict[str, SubplotWidget],
                    window_title: str,
                    ):
        self.subplot_widget_container = subplot_widget_container
        self.instrument_plot_items_map: Dict[str, List[SubplotItem]] = {}

        self._n_plots = 0
        self._n_rows = 0
        self._n_cols = 0
        self.init_layout()
        self.setWindowTitle(window_title)

    def init_layout(self):
        self._n_plots, self._n_rows, self._n_cols = self._calculate_window_dims()

        self.central_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.setCentralWidget(self.central_splitter)

        self.row_splitters: List[QtWidgets.QSplitter] = []

        for subplot_widget in self.subplot_widget_container.values():
            self.n_plot_update_signal.connect(subplot_widget.menu.subplot_num_changed)
            subplot_widget.menu.blockSignals(True)
            self.add_subplot_widget(subplot_widget)
            subplot_widget.menu.blockSignals(False)

        self.n_plot_update_signal.emit(self._n_plots)
        self.n_plot_update_signal.connect(self._set_splitter_stretch_factors)

    def _calculate_window_dims(self):
        n_plots = len(self.subplot_widget_container)
        nrows = np.floor(np.sqrt(n_plots)).astype(int)
        ncols = np.ceil(np.sqrt(n_plots))
        return n_plots, nrows, ncols

    def add_subplot_widget(self, subplot_widget: SubplotWidget):
        if len(self.row_splitters) == 0 or self.row_splitters[-1].count() >= self._n_cols:
            row_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
            self.central_splitter.addWidget(row_splitter)
            self.row_splitters.append(row_splitter)
        else:
            row_splitter = self.row_splitters[-1]

        row_splitter.addWidget(subplot_widget)
        self._connect_shared_vb_signals(subplot_widget)

    def remove_subplot_widget(self, subplot_widget: SubplotWidget):
        del self.subplot_widget_container[subplot_widget.title()]
        for row_splitter in self.row_splitters:
            row_splitter_index = row_splitter.indexOf(subplot_widget)
            if row_splitter_index != -1:
                row_splitter.widget(row_splitter_index).setParent(None)
                break
        self._restructure_subplots()
        self.n_plot_update_signal.emit(self._n_plots)

    def _restructure_subplots(self):
        for splitter in self.row_splitters:
            splitter.setParent(None)
        self.row_splitters = []

        self._n_plots, self._n_rows, self._n_cols = self._calculate_window_dims()

        for subplot_widget in self.subplot_widget_container.values():
            subplot_widget.menu.blockSignals(True)
            self.add_subplot_widget(subplot_widget)
            subplot_widget.menu.blockSignals(False)

    def _connect_shared_vb_signals(self, subplot_widget: SubplotWidget):
        for other_plot_widget in self.subplot_widget_container.values():
            subplot_widget.getPlotItem().vb.toggle_crosshairs_signal.connect(other_plot_widget.getPlotItem().vb.toggle_crosshairs)
            other_plot_widget.getPlotItem().vb.toggle_crosshairs_signal.connect(subplot_widget.getPlotItem().vb.toggle_crosshairs)

    def _set_splitter_stretch_factors(self, *args):
        for splitter in self.row_splitters:
            for i in range(splitter.count()):
                splitter.setStretchFactor(i, 1)
        for i in range(self.central_splitter.count()):
            self.central_splitter.setStretchFactor(i, 1)

    def resizeEvent(self, event):
        self._set_splitter_stretch_factors()
        super().resizeEvent(event)

    def setWindowTitle(self, arg):
        for subplot_widget in self.subplot_widget_container.values():
            subplot_widget.getPlotItem().vb.menu.set_window_title(arg)
        return super().setWindowTitle(arg)

    def add_close_event_callbacks(self, callback):
        self._close_event_callbacks.append(callback)

    def closeEvent(self, event):
        for callback in self._close_event_callbacks:
            callback(self)
