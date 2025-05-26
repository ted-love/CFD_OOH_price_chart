from __future__ import annotations
from typing import List, Optional, Tuple, Union, Dict, TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from timeseries.classes import TimeSeries, TimeSeriesContainer, TimeSeries
    from instruments.classes import InstrumentSpecs, InstrumentInfo, PriceInstrument, InstrumentContainer, InstrumentContainer
    from subplot_structure.classes import SubPlotStructure
    from exchanges.classes import ExchangeInfo
    from application import Application
    
import sys
from PySide6 import QtCore, QtWidgets
import workers
import pyqtgraph as pg
import custom_qt_classes.custom_widgets as custom_widgets
import utils
from custom_qt_classes.plot_data_item import CustomPlotDataItem, CustomScatterPlotDataItem
from custom_qt_classes.subplot_item import SubplotItem
from custom_qt_classes.view_box import CustomViewBox
from custom_qt_classes.subplot_widget import SubplotWidget
from custom_qt_classes.custom_widgets import MedianLegend
from mathematics import numerics as math_numerics


import numpy as np
from misc import themes

class CustomTextItem(pg.TextItem):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
    
    def setPos(self,*args, **kwargs):
        self.xx=args[0]
        

        
        args = list(args)
        args = tuple(args)
        super().setPos(*args, **kwargs)
        
    def pos_slot(self, view_box):
        
        view_range = view_box.viewRange()
        y_range = view_range[1]
        y_top = y_range[1]
        y_pos = y_top - 0.1 * (y_top - y_range[0])
        super().setPos(self.xx, y_pos)


def create_subplot_widget(plot_title, subplot_structure: SubPlotStructure):
        view_box_item = CustomViewBox()
        subplot_item = SubplotItem(subplot_structure,
                                    title=plot_title,
                                    viewBox=view_box_item,
                                    enableMenu=True,
                                    axisItems={"bottom" : custom_widgets.DateAxisItem(orientation="bottom"),
                                                "right"  : custom_widgets.CustomPriceAxisItem(orientation="right")})
        
        if not subplot_structure.ig_measuring_followers is None:
            median_legend = MedianLegend(offset=(1,1))
            subplot_item.median_legend = median_legend
            median_legend.setParentItem(view_box_item)  
            for follower_name, follower_object in subplot_structure.ig_measuring_followers.items():
                for leader_name, dynamic_median in follower_object.weight_metrics.dynamic_median_container.items():
                    name_str = f"{follower_name}/{leader_name}"
                    scatter_point = CustomScatterPlotDataItem(x=[0], y=[dynamic_median.median()], name=name_str, color="white")
                    median_legend.addItem(scatter_point)
                    follower_object.weight_metrics.add_update_callback(leader_name, scatter_point.median_response)
                    follower_object.weight_metrics.add_weight_changed_callback(leader_name, subplot_item.weight_response)
                    
                    for ts in follower_object.weight_metrics.weight_changes_container[leader_name]:
                        inf = pg.InfiniteLine(pos=ts, pen=pg.mkPen(color="red", style=QtCore.Qt.DashLine, width=1),angle=90)
                        subplot_item.addItem(inf)

        
        plot_widget = SubplotWidget(plotItem=subplot_item)
        return plot_widget

def create_subplot_widget_container(subplot_structure_container):
    plot_widget_container = {}
    for plot_title, subplot_structure in subplot_structure_container.items():
        subplot_widget = create_subplot_widget(plot_title, subplot_structure)
        subplot_plot_item = subplot_widget.getPlotItem()
        subplot_plot_item.setParent(subplot_widget)        
        plot_widget_container[subplot_widget.title()] = subplot_widget  
    return plot_widget_container

def add_plotdataitem_from_subplot_plot_item(subplot_plot_item: SubplotItem):
    colours = themes.get_colours()
    subplot_structure = subplot_plot_item.subplot_structure
    for instrument_name, colour in zip(subplot_structure.instrument_names, colours):       
        timeseries = subplot_structure.timeseries_container[instrument_name]     
                
        plot_data_item = CustomPlotDataItem.from_timeseries(timeseries,
                                                            subplot_structure.metric_attributes["minor"],
                                                            subplot_structure.metric_attributes["scale"],
                                                            colour
                                                            )
        subplot_plot_item.addItem(plot_data_item)
        
        
def add_data_to_subplots(subplot_widget_container: Dict[str, SubplotWidget]) -> None:
    for plot_title, subplot_widget in subplot_widget_container.items():
        subplot_plot_item = subplot_widget.getPlotItem()
        add_plotdataitem_from_subplot_plot_item(subplot_plot_item)
