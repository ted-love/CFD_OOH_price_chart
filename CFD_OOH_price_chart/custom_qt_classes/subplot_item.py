from __future__ import annotations
from typing import List, Optional, Tuple, Union, Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from subplot_structure.classes import SubPlotStructure
    from custom_qt_classes.view_box import CustomViewBox
    

import pyqtgraph as pg
from custom_qt_classes.custom_widgets import CustomLegend
from custom_qt_classes.plot_data_item import CustomPlotDataItem
from misc import themes
from PySide6 import QtCore
from custom_qt_classes.custom_widgets import MedianLegend
from custom_qt_classes.plot_data_item import CustomScatterPlotDataItem


class SubplotItem(pg.PlotItem):
    resizeSignal = QtCore.Signal()
    
    def __init__(self, subplot_structure: SubPlotStructure, *args, **kwargs):
        self.plotdataitem_container: Dict[str, CustomPlotDataItem] = {}
        self._plot_data_item_added_callbacks=[]
        self.subplot_structure=subplot_structure
        self._y_axis_scale = subplot_structure.metric_attributes["scale"]
        self.vb: CustomViewBox
        view_box: CustomViewBox = kwargs.get("viewBox", None)
        self.median_legend=None
        
        super().__init__(*args, **kwargs)
        view_box.setParent(self)     
        view_box.toggle_menu()
        
        self.current_x_min=None
        self.getAxis("left").hide()
        self.vb.name = self.titleLabel.text
        self.instrument_objects={}
        self.addLegend(offset=(-1, 1))
        
    def add_plotdataitem_added_callback(self, callback):
        self._plot_data_item_added_callbacks.append(callback)
    
    def addItem(self, item, *args, **kwargs):        
        if isinstance(item, CustomPlotDataItem):
            self.legend.addItem(item)
            instrument_name = item.name()
            self.plotdataitem_container[instrument_name] = item
            for callback in self._plot_data_item_added_callbacks:
                    callback(item)
        
        if isinstance(item, CustomScatterPlotDataItem):
            if item.name() in self.subplot_structure.followers:
                item.dynamic_median = self.subplot_structure.ig_measuring.dynamic_median_raw
                self.subplot_structure.ig_measuring.add_update_callbacks(item.set_dm)

        super().addItem(item, *args, **kwargs)
        
    def addLegend(self, offset=(30, 30), **kwargs):
        if self.legend is None:
            self.legend = CustomLegend(offset=offset, **kwargs)
            self.legend.setParentItem(self.vb)
            self.vb.add_legend(self.legend)
        return self.legend   
    
    def addMedianlegend(self, offset=(30, 30), **kwargs):
        if self.legend is None:
            self.legend = MedianLegend(offset=offset, **kwargs)
            self.legend.setParentItem(self.vb)
        return self.legend   

    def get_plot_data_items_for_instrument(self, instrument_name):
        return self.plotdataitem_container[instrument_name]
    
    def autoBtnClicked(self):
        self.vb.block_resizing(False)
        self.vb.set_interacting_off()
        self.vb.reset_view()
        self.vb.block_resizing(True)
        self.autoBtn.hide()

    def create_operation(self, expression):
        selected_names=[]
        display_names = list(self.plotdataitem_container.keys())
        for name in display_names:
            if name in expression:
                selected_names.append(name)
        if len(selected_names) == 1:
            new_name = expression
        if len(selected_names) > 2:
            new_name = f"theo_{self.titleLabel.text}"
        else:
            new_name = expression
        
        timeseries = self.subplot_structure.create_child_from_expression(selected_names,
                                                                         self.plotdataitem_container,
                                                                         self.y_scale(),
                                                                         expression=expression
                                                                        )
        
        colour = self._find_new_color()
        pen = pg.mkPen(color=colour)
        
        plot_curve = CustomPlotDataItem(timeseries=timeseries,
                                        metric_engine_major=timeseries.metric_engine,
                                        metric_engine_minor=timeseries.metric_engine_minor,
                                        metric_major=self.subplot_structure.metric_attributes["major"],
                                        metric_minor=self.subplot_structure.metric_attributes["minor"],
                                        y_scale=self.y_scale(),
                                        name=new_name,
                                        color=colour,
                                        pen=pen,
                                        )
        
        self.addItem(plot_curve)

    def _set_y_axis_metric(self, item: CustomPlotDataItem):
        if self._y_axis_scale is None:
            self._y_axis_scale=item.metric_major
        else:
            if item.metric_major != self._y_axis_scale:
                print(f"multiple different y-axis metric types on the same subplot: current {self.y_scale()}, new added item: {item.metric_major}")
                self._y_axis_scale = "multi"
    
    def reset_pct_point(self):
        for plotdataitem in self.plotdataitem_container.values():
            plotdataitem.reset_point()
        self.update()

    def _create_new_plotdataitem_set(self):
        prev_colours=[]
        for name, plotdataitem in self.plotdataitem_container.items():
            prev_colours.append(plotdataitem.current_color)
            self.removeItem(plotdataitem)
        
        for idx, (name, timeseries) in enumerate(self.subplot_structure.timeseries_container.items()):
            plotdataitem = CustomPlotDataItem.from_timeseries(timeseries, colour=prev_colours[idx])
            self.addItem(plotdataitem)  

    def removeItem(self, item):
        super().removeItem(item)
    

    def create_subsets(self, timestamp: float):
        
        for plotdataitem in self.plotdataitem_container.values():
            plotdataitem.create_subset(timestamp)
        """
        create_new_plotdata_flag = self.subplot_structure.create_subsets(timestamp)
        if create_new_plotdata_flag:
            self._create_new_plotdataitem_set()
        else:
            for plotdataitem in self.plotdataitem_container.values():
                plotdataitem.set_limits()
        """
        
        
        
    def change_y_scale(self, metric_type):
        self._y_axis_scale=metric_type
            
    def y_scale(self):
        return self._y_axis_scale
    
    
    def _find_new_color(self):
        used_colors=self.legend.used_colours

        colors = themes.get_colours()
        for color in colors:
            if color not in used_colors:
                break
        return color

    def toggle_instrument_visibility(self, name):
        plot_data_item = self.plotdataitem_container[name]
        plot_data_item.toggle_visibility()
    
    def toggle_plotdataitem_container(self, flag):
        self.blockSignals(True)
        if flag=="Add":
            for instrument in self.plotdataitem_container.values():
                instrument.show()
        else:
            self.blockSignals(True)
            for instrument in self.plotdataitem_container.values():
                instrument.hide()
                
        self.blockSignals(False)
        self.vb.set_limits()
        self.update()

    def weight_response(self, name, timestamp):
        inf = pg.InfiniteLine(pos=timestamp, pen=pg.mkPen(color="red", style=QtCore.Qt.DashLine, width=1),angle=90)
        self.addItem(inf)
    
    def resizeEvent(self, *args, **kwargs):
        super().resizeEvent(*args, **kwargs)
        self.vb.reset_view()