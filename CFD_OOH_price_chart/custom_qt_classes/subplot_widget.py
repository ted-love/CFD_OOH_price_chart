from __future__ import annotations
from typing import List, Optional, Tuple, Union, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from custom_qt_classes.view_box import CustomViewBox
    from custom_qt_classes.subplot_item import SubplotItem
import pyqtgraph as pg
from PySide6 import QtWidgets
from datetime import datetime   


from custom_qt_classes import builders as builders_custom_qt_classes

class SubplotWidget(pg.PlotWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blank=False
    
    def clone(self):
        subplot_plot_item = self.getPlotItem()
        subplot_structure = subplot_plot_item.subplot_structure
        new_subplot_structure = subplot_structure.clone_without_timeseries()
        new_subplot_widget = builders_custom_qt_classes.create_subplot_widget(self.title(), new_subplot_structure)
        builders_custom_qt_classes.add_plotdataitem_from_subplot_plot_item(new_subplot_widget.getPlotItem())
        return new_subplot_widget
    
    @property
    def subplot_structure(self):
        return self.getPlotItem().subplot_structure
    
    @property
    def menu(self):
        return self.getPlotItem().vb.menu
    
    def title(self) -> str:
        return self.getPlotItem().titleLabel.text
    
    def getViewBox(self) -> CustomViewBox:
        return self.getPlotItem().vb
    
    def getPlotItem(self) -> SubplotItem:
        return self.plotItem

class BlankWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blank=True
        self._title=datetime.now().timestamp()
    
    def title(self):
        return self._title