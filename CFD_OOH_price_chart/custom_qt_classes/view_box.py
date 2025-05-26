from __future__ import annotations
from typing import List, Optional, Tuple, Union, Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from custom_qt_classes.custom_widgets import CustomLegend
    from custom_qt_classes.data_helpers import DataLimits
    
import utils
import pyqtgraph as pg
import numpy as np
import utils
from PySide6 import QtCore
import pandas as pd
from datetime import datetime, time, timedelta
from dateutil import parser
import pytz
from custom_qt_classes.plot_data_item import CustomPlotDataItem
from custom_qt_classes.menu import CustomMenu
from timeseries.classes import TheoTimeSeries
from custom_qt_classes import data_helpers
    
class CustomViewBox(pg.ViewBox):
    mouse_pos_sig = QtCore.Signal(float, float)
    toggle_crosshairs_signal = QtCore.Signal()
    wheelXSignal = QtCore.Signal(object, tuple)
    
    def __init__(self, *args, **kwargs):
        kwargs["defaultPadding"]=0
        kwargs["enableMenu"]=False
        self._menu_on=False
        super().__init__(**kwargs)
        self.enableAutoRange("xy", enable=False)

        self.stored_data_limits={}
        self.current_x_data_min=None
        self.current_x_data_max=None
        self.current_y_data_min=None
        self.current_y_data_max=None
        self._resizing_blocked=True
        self._normalise_to_view=False
        self._interacting=False   
        self.x_buffer_rule=1/4
        self.y_buffer_rule=3/10
        self.prev_xmin=0

        self.view_data_limits: DataLimits=None
        
        self._full_data_limits=[[None, None], [None, None]]
        
        self.legend_x_coord=None
        self.no_data=True
        
        self.data_limits={}
        
        self._auto_scaling=False

        self.updating_x_range = False  
        self.updating_y_range=False
        self.instrument_data_items={}
        self.transformation_types=["Price", "Percentage"]
        self.vertical_line=None
        if datetime.now().weekday() == 0:
            self.global_x_min = pd.Timestamp(datetime.combine(datetime.now().date() - timedelta(days=1), time(17)), tz=pytz.timezone("America/Chicago")).timestamp() 
        else: 
            self.global_x_min=None
        
        self.crosshairs_on=False
        self._create_crosshairs()
        self.mouse_x, self.mouse_y = None, None
        self.mouse_pos_sig.connect(self.update_crosshairs_position)
        self.monday = True if datetime.now().weekday() == 0 else False

    def _create_crosshairs(self):
        self.crosshair_v = pg.InfiniteLine(pos=20, angle=90, pen={'color': 'grey', 'style': pg.QtCore.Qt.DashLine})
        self.crosshair_h = pg.InfiniteLine(pos=40, angle=0, pen={'color': 'grey', 'style': pg.QtCore.Qt.DashLine})
        
        self.crosshair_v.hide()
        self.crosshair_h.hide()
        self.addItem(self.crosshair_v)
        self.addItem(self.crosshair_h)

    def set_interacting_off(self, *args):
        self._interacting=False
    
    def setRange(self, rect=None, xRange=None, yRange=None, padding=None, update=True, disableAutoRange=True):
        if self._auto_scaling:
            
            if xRange is None:
                xRange = self.viewRange()[0]
            else:
                xRange = list(xRange)
            
            if yRange is None:
                yRange = self.viewRange()[1]
            else:
                yRange = list(yRange)
            
            self.view_data_limits.reset_view_limits()
            theo_series = []
            for plotdataitem in self.parent().plotdataitem_container.values():
                if plotdataitem.isVisible():
                    if isinstance(theo_series, TheoTimeSeries):
                        theo_series.append(theo_series)
                    else:
                        plotdataitem.buffer_from_view_limits(xRange)
                        self.view_data_limits.check_view(plotdataitem)
            for plotdataitem in theo_series:
                plotdataitem.timeseries.evaluate_timeseries()
                plotdataitem.buffer_from_view_limits(xRange)
                
                self.view_data_limits.check_view(plotdataitem)

            
            _, _, ymin_view, ymax_view = self.view_data_limits.view_limits()

            xmin_visible, xmax_visible, _, _, = self.view_data_limits.visible_limits()
            
            xRange[0] = max(xmin_visible, xRange[0])
            if xRange[0] > xmax_visible:
                xRange[0] = xmax_visible
                
            xRange = tuple(xRange)
            
            yRange[0] = ymin_view
            yRange[1] = ymax_view
            yRange = tuple(yRange)
                 
        super().setRange(rect=rect, xRange=xRange, yRange=yRange, padding=padding, update=update, disableAutoRange=disableAutoRange)
        x_lim, y_lim = self.viewRange()
        self.view_data_limits.set_view_limits(*x_lim, *y_lim)
    
    def filter_at_pos(self, x, snap_flag):
        self.block_resizing(True)
        self.parent().addItem(self.vertical_line)
        
        if snap_flag:
            self.parent().create_subsets(x)
        else:
            pass
        
        self.block_resizing(False)
        self.reset_view()
    
    def wheelEvent(self, ev, axis=None):
        self._interacting=True
        if self._auto_scaling:
            ev.accept()
            current_min, current_max = self.viewRange()[0]
            delta = ev.delta()
            
            scale_factor = 0.9 if delta > 0  else 1.1
            
            if current_min == self.view_data_limits.visible_limits()[0]:
                new_max = current_min + (current_max - current_min) * scale_factor
                self.setXRange(current_min, new_max, padding=0)
                return 
            
            new_min = current_max - (current_max - current_min) * scale_factor
            
            min_limit = self.view_data_limits.visible_limits()[0]
            new_min = max(new_min, min_limit)
            new_min = min(new_min, current_max - 1e-9) 
            self.setXRange(new_min, current_max, padding=0)
        else:
            return super().wheelEvent(ev, axis)

    def filter_data(self, dt_str):
        try:
            time_tuple = dt_str.split(",")
            if len(time_tuple) == 1:
                
                time_str = time_tuple[0]
                date_now = datetime.now().date()
            elif len(time_tuple) == 2:
                d, time_str = time_tuple
                date_now = datetime.now().date()
                date_now.replace(day=int(d))
                
            elif len(time_tuple) == 3:
                m ,d, time_str = time_tuple
                date_now = datetime.now().date()
                date_now.replace(month=int(m), day=int(d))
            
            elif len(time_tuple) == 4:
                y, m ,d, time_str = time_tuple
                date_now = datetime.now().date()
                date_now.replace(year=int(y), month=int(m), day=int(d))
            time_dt = parser.parse(time_str).time()
            ts_filter_time = datetime.combine(date_now, time_dt).timestamp()
            if self.vertical_line is None:
                self.vertical_line = pg.InfiniteLine(pos=ts_filter_time, angle=90, pen=pg.mkPen("red", style=QtCore.Qt.PenStyle.DashLine))
            else:
                self.vertical_line.setValue(ts_filter_time)
            self.parent().addItem(self.vertical_line)
            self.parent().create_subsets(ts_filter_time)
            
            self.reset_view()
        except:
            print(f"\n{dt_str} is not in the correct format")
    
    def transformation_action(self, transformation):
        for item in self.addedItems:
            if isinstance(item, CustomPlotDataItem):
                item.transform_data(transformation)

    
    def mouseDragEvent(self, ev, axis=None):
        self._interacting=True
        return super().mouseDragEvent(ev, axis)
    
    def add_legend(self, legend: CustomLegend):
        self.legend=legend
    
    def addItem(self, item, *args, **kwargs):
        super().addItem(item, *args, **kwargs)
        if isinstance(item, pg.InfiniteLine):
            return
        if isinstance(item, CustomPlotDataItem):
            self.instrument_data_items[item.opts["name"]] = item
            self.mouse_pos_sig.connect(lambda x, y, it=item: self._update_labels(x, y, it))
            self.legend.setItemLastValue(item)
            
            item.setParent(self)
            item.sigPlotChanged.connect(self.update_view_limits)
            item.sigVisibilityChanged.connect(self.reset_view)
            
            if self.no_data:
                self.block_resizing(False)
                self.view_data_limits = data_helpers.DataLimits(item)
                
                self.legend_x_coord = self.view_data_limits.visible_limits()[1]
                self.update_view_limits(item)
                self.no_data=False
            else:
                self.update_view_limits(item)
                
    def removeItem(self, item):
        self.reset_view()
        return super().removeItem(item)
                

    @property
    def create_operation(self):
        return self.parent().create_operation()

    def reset_pct_point(self):
        self.parent().reset_pct_point()
        self.reset_view()
        
    def update_view_limits(self,
                           plot_data_item: CustomPlotDataItem,
                           ):

        self.view_data_limits.check_set_limits(plot_data_item)
        if not self._interacting:
            xmin, xmax, ymin, ymax = self.view_data_limits.view_limits()
            if not self.view_data_limits.view_within_bounds(1, *self.viewRange()[1]):
                ymin, ymax = self.view_data_limits.calculate_limits_from_buffer(ymin, ymax, self.y_buffer_rule)
                self.set_y_limits(ymin, ymax)

            if not self.legend.legend_x_coord is None:
                xmax_val = self.legend.legend_x_coord
            else:
                xmax_val = self.legend_x_coord
                
            if not self.view_data_limits.view_within_bounds(0, self.viewRange()[0][0], xmax_val):
                self.set_x_limits(xmin, xmax)
            
    def set_y_limits(self, ymin, ymax):
        if not self._resizing_blocked:
            self.setYRange(ymin, ymax)      

    def set_x_limits(self, xmin, xmax):
        if not self._resizing_blocked:
            self.legend.updateSize()
            self.legend_x_coord = self.legend.width()
            ratio = self.legend.width() / self.boundingRect().topRight().x()
            d = xmax - xmin
            x_range_max = xmax + 2 * ratio * d
            self.legend_x_coord = xmax + ratio * d
            self.setXRange(xmin, x_range_max)
        
    def main_window_resize(self):
        self.block_resizing(False)
        self.reset_view()


    def reset_view(self):
        if not self.no_data:
            self.view_data_limits.reset_limits()
            self.view_data_limits.calculate_collection(self.parent().plotdataitem_container)
            
            xmin, xmax, ymin, ymax = self.view_data_limits.visible_limits()          
            self.set_x_limits(xmin, xmax)
            
            if not self._auto_scaling:
                ymin, ymax = self.view_data_limits.calculate_limits_from_buffer(ymin, ymax, self.y_buffer_rule)
            
            self.set_y_limits(ymin, ymax)
                
            for plotdataitem in self.parent().plotdataitem_container.values():
                plotdataitem.toggle_data_view(True)

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.MouseButton.RightButton:
            ev.accept()
            self.raiseContextMenu(ev)

    def raiseContextMenu(self, event):
        vb_coords = self.mapToView(event.pos())
        self.menu.popup(event.screenPos().toPoint(), vb_coords.x(), vb_coords.y())
    
    def toggle_menu(self):
        if not self._menu_on:
            self.menu = CustomMenu(self)
            self.parent().add_plotdataitem_added_callback(self.menu.update_instrument_toggle_menu)
        else:
            self.menu = None
    
    def block_resizing(self, flag):
        if flag:
            self._resizing_blocked=True
        else:
            self._resizing_blocked=False
    
    def create_operation(self, operation_expr):
        self.parent().create_operation(operation_expr)
    
    def toggle_crosshairs(self, text):
        if text == "On":
            flag=True
        else:
            flag=False
        
        if flag == self.crosshairs_on:
            return
        
        self.crosshairs_on = flag 
        self.legend.block_updates(self.crosshairs_on)    
        self.crosshairs_in_frame(self.crosshairs_on)

    def update_crosshairs_position(self, x, y):
        self.crosshair_v.setPos(x)
        self.crosshair_h.setPos(y)
    
    def crosshairs_in_frame(self, flag):
        if flag:
            self.crosshair_h.show()
            self.crosshair_v.show()
        else:
            self.mouse_x, self.mouse_y = None, None
            self.crosshair_h.hide()
            self.crosshair_v.hide()
            for plot_data_item in self.instrument_data_items.values():
                y_value = plot_data_item.yData[-1]
                plot_data_item.legend_label.setText(f"{plot_data_item.name()}: {utils.format_price(y_value)}")

    def hoverEvent(self, ev):
        if ev.isEnter():            
            if self.crosshairs_on:
                self.crosshairs_in_frame(True)
            
        elif ev.isExit():
            self.crosshairs_in_frame(False)
            
        else:
            if self.crosshairs_on:
                mouse_pos = ev.pos()  
                vb_coords = self.mapToView(mouse_pos)
                self.mouse_x, self.mouse_y = vb_coords.x(), vb_coords.y()
                self.mouse_pos_sig.emit(self.mouse_x, self.mouse_y)

    def _update_labels(self, x, y, plot_data_item):
        idx = np.searchsorted(plot_data_item.xData, x, side='right') - 1
        y_value = plot_data_item.yData[idx]
        self.legend.setText(y_value, plot_data_item)

    
    def clone(self):
        new_vb = CustomViewBox()
        new_vb.toggle_menu()
        return new_vb
    
            
    def toggle_y_scale(self, scale):
        match scale:
            case "returns (%)":
                scale="pct"
            case "log-returns":
                scale="log"
            case "returns":
                scale="decimal"
            case "Price":
                scale="base"
                
        if scale == self.parent().y_scale():
            return 

        theo_plotdataitem=[]
        
        xmin_old, xmax_old, _, _ = self.view_data_limits.view_limits()
        self.view_data_limits.reset_view_limits()
        
        for plotdataitem in self.parent().plotdataitem_container.values():
            if isinstance(plotdataitem.timeseries, TheoTimeSeries):
                theo_plotdataitem.append(plotdataitem)
            else:
                plotdataitem.change_y_scale(scale)
                plotdataitem.update_from_timeseries_update(plotdataitem.timeseries)
            
                
        for plotdataitem in theo_plotdataitem:
            plotdataitem.timeseries.evaluate_timeseries()
            plotdataitem.update_from_timeseries_update(plotdataitem.timeseries)

        self.view_data_limits.calculate_collection(self.parent().plotdataitem_container)
        self.view_data_limits.set_axis_view_limit(0, xmin_old, xmax_old)
        
        
        _, _, ymin, ymax = self.view_data_limits.view_limits()
        if not self._interacting:
            self.set_y_limits(*self.view_data_limits.calculate_limits_from_buffer(ymin, ymax, self.y_buffer_rule))
        else:
            self.set_y_limits(ymin, ymax)
        
        self.parent().change_y_scale(scale)
        self.parent().update()

    def toggle_auto_scaling(self, text):
        if text == "On":
            flag=True
        else:
            flag=False
        if flag == self._auto_scaling:
            return
        
        self.reset_view()
        self._interacting=flag
        
        if flag:
            for plotdataitem in self.parent().plotdataitem_container.values():
                                
                self.sigXRangeChanged.connect(plotdataitem.update_from_view_change)
        else:
            for plotdataitem in self.parent().plotdataitem_container.values():
                self.sigXRangeChanged.disconnect(plotdataitem.update_from_view_change)
                    
        self._auto_scaling=flag
        
    def toggle_normalise_data_to_view(self, text):
        if text == "On":
            flag=True
        else:
            flag=False
        
        if flag == self._normalise_to_view:
            return

        self._normalise_to_view=flag
        
        
        if flag:
            for plotdataitem in self.parent().plotdataitem_container.values():
                plotdataitem.set_normalise_to_view(True)
        else:
            for plotdataitem in self.parent().plotdataitem_container.values():
                plotdataitem.set_normalise_to_view(False)
                
        self.parent().update()
        
        