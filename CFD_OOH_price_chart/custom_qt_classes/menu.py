from __future__ import annotations
from typing import List, Optional, Tuple, Union, Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from subplot_structure.classes import SubPlotStructure
    from custom_qt_classes.view_box import CustomViewBox
    from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent
    from custom_qt_classes.plot_data_item import CustomPlotDataItem
    from custom_qt_classes.view_box import CustomViewBox
    from application import Application

from PySide6 import QtWidgets, QtCore
from custom_qt_classes.subplot_widget import SubplotWidget  
from datetime import datetime   
import pyqtgraph as pg


class WindowMenu(QtWidgets.QWidget):
    def __init__(self, subplot_widget_container: Dict[str, SubplotWidget] | None=None) -> None:
        super().__init__()
        self.combobox_y_metric=None
        self.combobox_hover=None
        self.combobox_auto_scale=None
        self.combobox_normalise_to_view=None
        
        self.setLayout(QtWidgets.QHBoxLayout())
        
        
        self._create_y_metric_options()
        self._create_hover_options()
        self._create_auto_scale_options()
        self._create_normalise_to_view_options()
        
        
        if not subplot_widget_container is None:
            for subplot_widget in subplot_widget_container.values():
                self.connect_subplot_widget_to_signals(subplot_widget)
        
    def _create_y_metric_options(self):
        container = QtWidgets.QWidget()
        label = QtWidgets.QLabel("Y-axis Scale")
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.combobox_y_metric = QtWidgets.QComboBox()
        self.combobox_y_metric.addItems(["returns (%)", "returns", "log-returns", "Price"])
        self.combobox_y_metric.setCurrentIndex(0)  
        layout.addWidget(label)
        layout.addWidget(self.combobox_y_metric)
        container.setLayout(layout)
        
        self.layout().addWidget(container)
        

    def _create_hover_options(self):
        container = QtWidgets.QWidget()
        label = QtWidgets.QLabel("Crosshairs")
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.combobox_hover = QtWidgets.QComboBox()
        self.combobox_hover.addItems(["On", "Off"])
        self.combobox_hover.setCurrentIndex(1)  
        layout.addWidget(label)
        layout.addWidget(self.combobox_hover)
        container.setLayout(layout)
        
        self.layout().addWidget(container)
        
    def _create_auto_scale_options(self):
        container = QtWidgets.QWidget()
        label = QtWidgets.QLabel("Auto Scale")
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.combobox_auto_scale = QtWidgets.QComboBox()
        self.combobox_auto_scale.addItems(["On", "Off"])
        self.combobox_auto_scale.setCurrentIndex(1)  

        layout.addWidget(label)
        layout.addWidget(self.combobox_auto_scale)
        container.setLayout(layout)
        
        self.layout().addWidget(container)

    def _create_normalise_to_view_options(self):
        container = QtWidgets.QWidget()
        label = QtWidgets.QLabel("Normalise % to View")
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.combobox_normalise_to_view = QtWidgets.QComboBox()
        self.combobox_normalise_to_view.addItems(["On", "Off"])
        self.combobox_normalise_to_view.setCurrentIndex(1)  
        self.combobox_normalise_to_view.currentTextChanged.connect(self._grey_out_auto_scale)

        layout.addWidget(label)
        layout.addWidget(self.combobox_normalise_to_view)
        container.setLayout(layout)
        
        self.layout().addWidget(container)


    def _set_hover_options(self, subplot_widget_container: Dict[str, SubplotWidget]):
        container = QtWidgets.QWidget()
        label = QtWidgets.QLabel("Crosshairs")
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.combobox_hover = QtWidgets.QComboBox()
        self.combobox_hover.addItems(["On", "Off"])
        self.combobox_hover.setCurrentIndex(1)  
        for subplot_widget in subplot_widget_container.values():
            self.combobox_hover.currentTextChanged.connect(subplot_widget.getViewBox().toggle_crosshairs)

        layout.addWidget(label)
        layout.addWidget(self.combobox_hover)
        container.setLayout(layout)
        
        self.layout().addWidget(container)

    def _set_auto_scale_options(self, subplot_widget_container: Dict[str, SubplotWidget]):
        container = QtWidgets.QWidget()
        label = QtWidgets.QLabel("Auto Scale")
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.combobox_auto_scale = QtWidgets.QComboBox()
        self.combobox_auto_scale.addItems(["On", "Off"])
        self.combobox_auto_scale.setCurrentIndex(1)  
        for subplot_widget in subplot_widget_container.values():
            self.combobox_auto_scale.currentTextChanged.connect(subplot_widget.getViewBox().toggle_auto_scaling)
        layout.addWidget(label)
        layout.addWidget(self.combobox_auto_scale)
        container.setLayout(layout)
        self.layout().addWidget(container)

    def _grey_out_auto_scale(self, flag):
        if flag == "On":
            if self.combobox_auto_scale.currentIndex() == 1:
                self.combobox_auto_scale.setCurrentText("On")
            self.combobox_auto_scale.setEnabled(False)
        else:
            self.combobox_auto_scale.setEnabled(True)


    def _set_normalise_to_view_options(self, subplot_widget_container: Dict[str, SubplotWidget]):
        container = QtWidgets.QWidget()
        label = QtWidgets.QLabel("Normalise % to View")
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.combobox_normalise_to_view = QtWidgets.QComboBox()
        self.combobox_normalise_to_view.addItems(["On", "Off"])
        self.combobox_normalise_to_view.setCurrentIndex(1)  
        for subplot_widget in subplot_widget_container.values():
            self.combobox_normalise_to_view.currentTextChanged.connect(subplot_widget.getViewBox().toggle_normalise_data_to_view)
            
        layout.addWidget(label)
        layout.addWidget(self.combobox_normalise_to_view)
        container.setLayout(layout)
        
        self.layout().addWidget(container)

    def connect_subplot_widget_to_signals(self, subplot_widget: SubplotWidget):
        self.combobox_y_metric.currentTextChanged.connect(subplot_widget.getViewBox().toggle_y_scale)
        self.combobox_hover.currentTextChanged.connect(subplot_widget.getViewBox().toggle_crosshairs)
        self.combobox_auto_scale.currentTextChanged.connect(subplot_widget.getViewBox().toggle_auto_scaling)
        self.combobox_normalise_to_view.currentTextChanged.connect(subplot_widget.getViewBox().toggle_normalise_data_to_view)

        text_y_metric = self.combobox_y_metric.currentText()
        text_hover = self.combobox_hover.currentText()
        text_autoscale = self.combobox_auto_scale.currentText()
        text_normalise = self.combobox_normalise_to_view.currentText()

        subplot_widget.getViewBox().toggle_y_scale(text_y_metric)
        subplot_widget.getViewBox().toggle_crosshairs(text_hover)
        subplot_widget.getViewBox().toggle_auto_scaling(text_autoscale)
        subplot_widget.getViewBox().toggle_normalise_data_to_view(text_normalise)
        
        
        

    def disconnect_subplot_widget_from_signals(self, subplot_widget: SubplotWidget):
        self.combobox_hover.currentTextChanged.disconnect(subplot_widget.getViewBox().toggle_crosshairs)
        self.combobox_auto_scale.currentTextChanged.disconnect(subplot_widget.getViewBox().toggle_auto_scaling)
        self.combobox_normalise_to_view.currentTextChanged.disconnect(subplot_widget.getViewBox().toggle_normalise_data_to_view)


    def disconnect_all_slots(self):
        return 
        if self.combobox_hover:
            self.combobox_hover.currentTextChanged.disconnect()
        if self.combobox_auto_scale:
            self.combobox_auto_scale.currentTextChanged.disconnect()
        if self.combobox_normalise_to_view:
            self.combobox_normalise_to_view.currentTextChanged.disconnect()



class CustomMenu(QtWidgets.QMenu):
    window_structure_signal = QtCore.Signal(str, tuple, SubplotWidget)
    def __init__(self, view_box: CustomViewBox, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view_box=view_box
        self.vb_x=0
        self.vb_y=0
        self.menu_instrument_toggle=None
        self.menu_operation=None
        self.menu_change_x_limits=None
        self.menu_crosshair_menu=None
        self.menu_format_windows=None
        self._toggle_instrument_map={}
        self.window_title=None
        self.n_subplots=0
        self.more_than_1_subplot=False
        self.window_titles=[]
        self._window_menu_on=True
        self.pop_out_subplot_action=None
        self.move_subplot_actions={}
        self._actions_instrument_toggle=[]
        self.init_menus()
    
    
        
    def init_menus(self):
        self._init_parent_menus()
        self._init_submenus()
        self._init_actions()
    
    def _init_parent_menus(self):
        self.menu_instrument_toggle = self.addMenu("Toggle Instruments")
        self.addSeparator()
        self.menu_operation = self.addMenu("Create Operation")
        self.addSeparator()
        self.menu_change_x_limits = self.addMenu("Adjust returns point")
        self.addSeparator()

        
    def _init_actions(self):
        self._create_instrument_toggle_menu()
        self._create_operation_menu()
        if self._window_menu_on:
            self._window_structure_menu()

    
    def _add_toggle_instrument_action(self, plotdataitem: CustomPlotDataItem):
        instrument_action = self.menu_sub_instrument_toggle_single.addAction(plotdataitem.name())
        instrument_action.setCheckable(True) 
        instrument_action.setChecked(True) 
        instrument_action.toggled.connect(plotdataitem.toggle_visibility)
        self._actions_instrument_toggle.append(instrument_action)
        
    def toggle_window_structure_menu(self, n_subplots):
        if n_subplots > 1:
            self.menu_format_windows = self.addMenu("Format Windows")
            self.addSeparator()
        else:
            self._window_menu_on=False

    def popup(self, q_point, x, y):
        if not self.menu_format_windows is None:
            menu_action = self.menu_format_windows.menuAction()
            self.removeAction(menu_action)
            self.menu_format_windows = self.addMenu("Format Windows")
            self._window_structure_menu()
        self.menu_change_x_limits.clear()
        self._create_returns_adjustment_menu(x, y)
        super().popup(q_point)

    def _create_instrument_toggle_menu(self):
        def _show_all():
            for action in self._actions_instrument_toggle:
                action.setChecked(True)
        def _hide_all():
            for action in self._actions_instrument_toggle:
                action.setChecked(False)

        subplot_plot_item = self.view_box.parent()
        for plotdataitem in subplot_plot_item.plotdataitem_container.values():
            self._add_toggle_instrument_action(plotdataitem)
            
        add_all_action = self.menu_sub_instrument_toggle_container.addAction("Show")
        remove_all_action = self.menu_sub_instrument_toggle_container.addAction("Hide")

        add_all_action.triggered.connect(lambda: _show_all())
        remove_all_action.triggered.connect(lambda: _hide_all())
        
    
    def _init_submenus(self):
        self.menu_sub_instrument_toggle_single = self.menu_instrument_toggle.addMenu("Toggle Single")
        self.menu_sub_instrument_toggle_container = self.menu_instrument_toggle.addMenu("Toggle All")
        
    def _create_returns_adjustment_menu(self, x, y):
        snap_action = self.menu_change_x_limits.addAction(f"Snap Chart at {datetime.fromtimestamp(x).strftime("%H:%M:%S")}")
        snap_action.triggered.connect(lambda: (self.view_box.filter_at_pos(x, True), self.close()))
        default_point_action = self.menu_change_x_limits.addAction("Reset Default Point")
        default_point_action.triggered.connect(lambda: self.view_box.reset_pct_point())

        
        
    def _create_operation_menu(self):
        text_action = QtWidgets.QWidgetAction(self.menu_operation)
        subplot_plot_item = self.view_box.parent() 
        line_edit = QtWidgets.QLineEdit(self.menu_operation)
        line_edit.setPlaceholderText("Type name  →  Enter")
        text_action.setDefaultWidget(line_edit)
        self.menu_operation.addAction(text_action)
        self.menu_operation.aboutToShow.connect(lambda: QtCore.QTimer.singleShot(0, line_edit.setFocus))
        line_edit.returnPressed.connect(lambda: (subplot_plot_item.create_operation(line_edit.text()), self.menu_operation.close()))

    def set_window_title(self, title):
        self.window_title=title
        
    def _window_structure_menu(self):
        
        if self.more_than_1_subplot:
            action = "Pop-Out"
            self.pop_out_subplot_action = self.menu_format_windows.addAction("Pop-Out Subplot")
            args1 = action, (self.window_title, ""), self.view_box.parent().parent()
            self.pop_out_subplot_action.triggered.connect(lambda _: self.window_structure_signal.emit(*args1))
        if len(self.window_titles) > 1:
            action = "Move"
            for other_window_title in self.window_titles:
                if other_window_title != self.window_title:
                    move_subplot_action = self.menu_format_windows.addAction(f"Move to {other_window_title}")
                    args2 = action, (self.window_title, other_window_title), self.view_box.parent().parent()
                    move_subplot_action.triggered.connect(lambda _: self.window_structure_signal.emit(*args2))
                    self.move_subplot_actions[other_window_title] = move_subplot_action
                    
        
    @QtCore.Slot(int)
    def window_titles_slot(self, n):
        self.window_titles=n
    
    @QtCore.Slot(int)
    def subplot_num_changed(self, n):
        if n > 1:
            self.more_than_1_subplot=True
        else:
            self.more_than_1_subplot=False
    
    def update_instrument_toggle_menu(self, item: CustomPlotDataItem):
        self._add_toggle_instrument_action(item)