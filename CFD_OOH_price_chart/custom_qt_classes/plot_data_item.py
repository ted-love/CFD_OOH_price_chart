from __future__ import annotations

from typing import List, Optional, Tuple, Union, Dict, TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from timeseries.classes import TimeSeries, TimeSeries
    from mathematics.numerics import MetricConverter
    from custom_qt_classes.view_box import CustomViewBox

import pyqtgraph as pg
from PySide6 import QtCore, QtGui

from timeseries.classes import TimeSeries, TheoTimeSeries
from custom_qt_classes import data_helpers
from mathematics import numerics as math_numerics
import copy

class CustomPlotDataItem(pg.PlotDataItem):
    sigVisibilityChanged = QtCore.Signal(object)
    color_changed = QtCore.Signal(object)
    
    def __init__(self,
                 timeseries: TimeSeries,
                 metric_engine_major: MetricConverter=None,
                 metric_engine_minor: MetricConverter=None,
                 metric_major: str=None,
                 metric_minor: str=None,
                 y_scale: str=None,
                 view_range: List[List[float]]=None,
                 name: str=None,
                 pen: QtGui.QPen=None,
                 color: str=None,
                 alarm_color: str=None,
                 *args,
                 **kwargs
                 ):

        self.timeseries=timeseries
        self.metric_engine_major=metric_engine_major
        self.metric_engine_minor=metric_engine_minor
        self._metric_engine_full_data=metric_engine_major
        self.metric_major=metric_major
        self.y_scale=y_scale
        self.metric_minor=metric_minor
        self.legend_label=None
        self.current_color=color
        self.regular_color=color
        self._normalise_to_view=False
        self._plot_on_update=True
        self._display_full=True
        self.major_value=None
        self.minor_value=None
        self.dynamic_median=None
        self._update_buffered=False
        self.x_min_full=None
        self._subset=False
        self._update_callbacks = []
        
        if self.metric_engine_minor is None:
            self.metric_engine_minor=math_numerics.MetricConverter(metric=metric_minor,
                                                                   scale=y_scale
                                                                   )
        if alarm_color is None:
            self.alarm_color=self.regular_color
        else:
            self.alarm_color=alarm_color
        
        self._series_container_full = data_helpers.SeriesContainer(timeseries=self.timeseries,
                                                                   metric_engine=copy.deepcopy(metric_engine_major))
        
        self._series_container_view = data_helpers.SeriesContainer(timeseries=self.timeseries,
                                                                   metric_engine=copy.deepcopy(metric_engine_major))
        if not view_range is None:
            self._series_container_view.update_from_view_range(*self._series_container_full.source_series(),
                                                               view_range)
        x, y = self._series_container_view.processed_series()   
        
        self.x_min_full=self._series_container_full.limits()[0]
        self.major_value=self._series_container_full.last_y

        super().__init__(x=x, y=y, name=name, pen=pen, skipFiniteCheck=True, *args, **kwargs)
        self.timeseries.add_update_callback(self.update_from_timeseries_update)


    def update_from_timeseries_update(self, timeseries: TimeSeries|TheoTimeSeries):
        self.minor_value = self.metric_engine_minor.display_function(*timeseries.parent_minor_metrics[self.metric_minor])
        self._series_container_full.update_from_update_response(timeseries)
        for callback in self._update_callbacks:
            callback(self)
        
        if self._display_full:
            self._series_container_view.update_from_data_metrics(self._series_container_full)
        else:
            if self.parent().viewRange()[0][1] > self._series_container_full.last_x:
                self._series_container_view.update_on_last_idx_min(*self._series_container_full.source_series())
        self._process_update()        
        
    def create_subset(self, xmin):
        self._series_container_full.make_subset(xmin)
        self._series_container_view.update_from_data_metrics(self._series_container_full)
        self._process_update()
        
    def _process_update(self):
        if self._normalise_to_view:
            self.major_value=self._series_container_view.last_y
        else:
            self.major_value=self._series_container_full.last_y
        super().setData(*self._series_container_view.processed_series())
        
        
    def reset_point(self):
        self._series_container_full = data_helpers.SeriesContainer(timeseries=self.timeseries,
                                                                   metric_engine=copy.deepcopy(self._metric_engine_full_data))
        self._series_container_view.update_from_data_metrics(self._series_container_full)
        
        if self._normalise_to_view:
            self.major_value=self._series_container_view.last_y
        else:
            self.major_value=self._series_container_full.last_y
        super().setData(*self._series_container_view.processed_series())

    def toggle_data_view(self, flag):
        self._display_full=flag

    def change_y_scale(self, scale):
        self.y_scale=scale
        self._series_container_view.scale(scale)
        self._series_container_full.scale(scale)
        self.metric_engine_minor.change_scale(scale)
        super().setData(*self._series_container_view.processed_series())

    def set_normalise_to_view(self, flag):
        self._normalise_to_view=flag
        self._display_full=flag
        
        if flag:
            self._series_container_view.normalise_to_view=True
        else:
            self._series_container_view.normalise_to_view=False
            full_view_param = self._series_container_full.metric_engine.static_param
            self._series_container_view.metric_engine.change_static_param(full_view_param)
    
    def toggle_display_full(self, flag):
        self._display_full=flag
    
    def buffer_from_view_limits(self, 
                                newRange: List[List[float]]
                                ):
        self._display_full=False
        self._series_container_view.update_from_view_range(*self._series_container_full.source_series(),
                                                           newRange)
    
    def update_from_view_change(self,
                                vb: CustomViewBox,
                                newRange: List[List[float]]
                                ) -> None:
        self._display_full=False
        if isinstance(self.timeseries, TheoTimeSeries):
            self.timeseries.update_displayed_dataset_bounds(vb, newRange)

        if not self._update_buffered:

            
            self._series_container_view.update_from_view_range(*self._series_container_full.source_series(),
                                                               newRange)
        else:
            self._update_buffered=False
        self._process_update()
    
    def view_limits(self):
        return self._series_container_view.limits()
                
    def dataset_limits(self):
        return self._series_container_full.limits()
    
    def view_last_values(self):
        return self._series_container_view.last_values()

    def view_set(self):
        return self._series_container_view.processed_series()

    def dataset(self):
        return self._series_container_full.processed_series()

    def dataset_last_values(self):
        return self._series_container_full.last_values()
    
    def hide(self):
        if self.isVisible():
            super().hide()    
            self.sigVisibilityChanged.emit(self)

    def show(self):
        if not self.isVisible():
            super().show()    
            self.sigVisibilityChanged.emit(self)

    @QtCore.Slot()
    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
        
    def check_alarm_value(self, alarm_on):
        if alarm_on:
            if self.current_color == self.regular_color:
                self.current_color=self.alarm_color
                self.setPen(pg.mkPen(self.alarm_color, width=1))
                self.update()
                self.color_changed.emit(self)
        else:
            if self.current_color == self.alarm_color:
                self.current_color=self.regular_color
                self.setPen(pg.mkPen(self.regular_color, width=1))
                self.update()
                self.color_changed.emit(self)
    
    @classmethod
    def from_timeseries(cls,
                        timeseries: TimeSeries,
                        metric_minor: str,
                        scale: str,
                        colour: str,
                        view_range: List[List[float]]=None,
                        ) -> CustomPlotDataItem:
        new_data_item = cls(timeseries=timeseries,
                            metric_engine_major=timeseries.metric_engine,
                            metric_major=timeseries.metric_type,
                            metric_minor=metric_minor,
                            y_scale=scale,
                            view_range=view_range,
                            name=timeseries.name,
                            pen=pg.mkPen(color=colour),
                            width=1,
                            color=colour
                            )
        new_data_item.setCurveClickable(True)
        return new_data_item

    def add_update_callback(self, callback: Callable):
        self._update_callbacks.append(callback)


        
    
    
class CustomScatterPlotDataItem(pg.ScatterPlotItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.median=kwargs["y"][0]
        self.color="red"
    
    def median_response(self, weight_metrics: float):
        self.median=weight_metrics
        super().setData(x=[0], y=[weight_metrics])
    