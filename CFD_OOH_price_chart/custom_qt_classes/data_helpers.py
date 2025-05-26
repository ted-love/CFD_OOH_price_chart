from typing import List, Optional, Tuple, Union, Dict, TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from timeseries.classes import TimeSeries, TimeSeries
    from mathematics.numerics import MetricConverter
    from custom_qt_classes.data_helpers import SeriesContainer
    from custom_qt_classes.plot_data_item import CustomPlotDataItem

    
    

from timeseries.classes import TimeSeries, TheoTimeSeries
from dataclasses import dataclass, field, InitVar
import numpy as np
from custom_numpy import BufferArray
from mathematics.numerics import MetricConverter

@dataclass(slots=True, kw_only=True)
class SeriesContainer:
    timeseries: InitVar[Union["TimeSeries", "TheoTimeSeries"]]
    name: str = field(default_factory=lambda: None)
    metric_engine: MetricConverter = field(default_factory=lambda: None)
    xmin: float = field(default_factory=lambda: None)
    xmax: float = field(default_factory=lambda: None)
    ymin: float = field(default_factory=lambda: None)
    ymax: float = field(default_factory=lambda: None)
    last_x: float = field(default_factory=lambda: None)
    last_y: float = field(default_factory=lambda: None)
    x_source: BufferArray|np.ndarray = field(default_factory=lambda: None)
    y_source: BufferArray|np.ndarray = field(default_factory=lambda: None)
    x_processed: BufferArray|np.ndarray = field(default_factory=lambda: None)
    y_processed: BufferArray|np.ndarray = field(default_factory=lambda: None)
    
    last_idx_min: int|None = field(default_factory=lambda: None)
    last_idx_max: int|None = field(default_factory=lambda: None)
    normalise_to_view: bool = field(default_factory=lambda: False)
    _subset: bool = field(default_factory=lambda: False)
    _subset_idx: int|None = field(default_factory=lambda: None)
    view_range: List[List[float]] = field(default_factory=lambda: None)
    
    def __post_init__(self, timeseries: Union["TimeSeries", "TheoTimeSeries"]):
        self.name = timeseries.name
        self.update_from_series(*timeseries.get_data())
                
    def update_from_series(self,
                           x: BufferArray|np.ndarray,
                           y: BufferArray|np.ndarray
                           ) -> Tuple[BufferArray, BufferArray]|Tuple[np.ndarray, np.ndarray]:
        self.x_source=x
        self.y_source=y
                
        self.x_processed=self.x_source
        self.y_processed=self.metric_engine.convert_to_display(self.metric_engine.static_param, self.y_source)
        
        self.xmin, self.xmax = self.x_processed.min(), self.x_processed.max()
        self.ymin, self.ymax = self.y_processed.min(), self.y_processed.max()
        self.last_x = self.x_processed[-1]
        self.last_y = self.y_processed[-1]
        
        
    
    def update_on_last_idx_min(self,
                               x: BufferArray|np.ndarray,
                               y: BufferArray|np.ndarray,
                               ) -> None:
        self.update_from_series(x[self.last_idx_min:], y[self.last_idx_min:])
    
    def update_from_view_range(self,
                               x: BufferArray|np.ndarray,
                               y: BufferArray|np.ndarray,
                               view_range: List[List[float]]
                               ) -> None:
        self.view_range=view_range
        self.last_idx_min = np.searchsorted(x, view_range[0], side="right")  - 1
        self.last_idx_max = np.searchsorted(x, view_range[1], side="left")
        if self.last_idx_min < 0:
            self.last_idx_min=0
        
        if self.normalise_to_view:
            self.metric_engine.change_static_param(y[self.last_idx_min])
        
        self.update_from_series(x[self.last_idx_min:self.last_idx_max], y[self.last_idx_min:self.last_idx_max])
    
    def scale(self, scale: str) -> None:
        self.metric_engine.change_scale(scale)
        self.update_from_series(self.x_source, self.y_source)        
    
    def update_from_update_response(self,
                                    timeseries: Union["TimeSeries", "TheoTimeSeries"]
                                    ) -> None:
        if self._subset:
            x_source, y_source = timeseries.get_data()
            self.x_source, self.y_source = x_source[self._subset_idx:], y_source[self._subset_idx:]
        else:
            self.x_source, self.y_source = timeseries.get_data()
        
        self.x_processed = self.x_source
        self.y_processed = self.metric_engine.convert_to_display(self.metric_engine.static_param, self.y_source)
        self.update_from_point(self.x_processed[-1], self.y_processed[-1])
        
    def update_from_point(self,
                          x: float,
                          y: float
                          ) -> None:
        self.last_x = x
        self.last_y = y
        
        if x > self.xmax:
            self.xmax = x
        elif x < self.xmin:
            self.xmin = x
        if y > self.ymax:
            self.ymax = y
        elif y < self.ymin:
            self.ymin = y
    
    def make_subset(self, timestamp):
        self._subset=True
        
        self._subset_idx = np.searchsorted(self.x_source, timestamp, side="right")  - 1
        
        self.x_source = self.x_source[self._subset_idx:]
        self.y_source = self.y_source[self._subset_idx:]
        
        if self._subset_idx < 0:
            self._subset_idx=0
        
        self.metric_engine.change_static_param(self.y_source[0])
        
        self.last_idx_min = self._subset_idx
        
        self.update_from_series(self.x_source, self.y_source)
        
    def last_values(self):
        return self.last_x, self.last_y
            
    def limits(self):
        return self.xmin, self.xmax, self.ymin, self.ymax

    def source_series(self):
        return self.x_source, self.y_source
    
    def processed_series(self):
        return self.x_processed, self.y_processed
                
    def update_from_data_metrics(self,
                                 data_metrics_object: "SeriesContainer"
                                 ) -> None:
        self.xmin = data_metrics_object.xmin
        self.xmax = data_metrics_object.xmax
        self.ymin = data_metrics_object.ymin
        self.ymax = data_metrics_object.ymax
        self.last_x = data_metrics_object.last_x
        self.last_y = data_metrics_object.last_y
        self.x_processed = data_metrics_object.x_processed
        self.y_processed = data_metrics_object.y_processed

@dataclass(slots=True)
class Limit:
    xmin: float|None = field(default_factory=lambda: None)
    xmax: float|None = field(default_factory=lambda: None)
    ymin: float|None = field(default_factory=lambda: None)
    ymax: float|None = field(default_factory=lambda: None)

    def check(self, xmin, xmax, ymin, ymax):
        if self.xmin is None or xmin < self.xmin:
            self.xmin = xmin
        if self.xmax is None or xmax > self.xmax:
            self.xmax = xmax
        if self.ymin is None or ymin < self.ymin:
            self.ymin = ymin
        if self.ymax is None or ymax > self.ymax:
            self.ymax = ymax

    def set(self, xmin, xmax, ymin, ymax):
        self.xmin=xmin
        self.xmax=xmax
        self.ymin=ymin
        self.ymax=ymax
    
    def reset(self):
        self.xmin=None
        self.xmax=None
        self.ymin=None
        self.ymax=None

    
@dataclass(slots=True)
class DataLimits:
    """
    
    *** IMPORTANT ***
    
    This holds the limits of the data, NOT the actual view. In other words, the dataset_view holds the limits of the data given the current view of the viewbox. 
    
    """
    plot_data_item: InitVar["CustomPlotDataItem"]
    dataset_view: Limit = field(default_factory=lambda: None)
    dataset_visible: Limit = field(default_factory=lambda: None)
    dataset_all: Limit = field(default_factory=lambda: None)
    
    def __post_init__(self, plot_data_item: "CustomPlotDataItem"):
        self.dataset_view = Limit(*plot_data_item.view_limits())
        self.dataset_visible = Limit(*plot_data_item.dataset_limits())
        self.dataset_all = Limit(*plot_data_item.dataset_limits())
        
    
    def check_view(self, plot_data_item: "CustomPlotDataItem"):
        self.dataset_view.check(*plot_data_item.view_limits())
    
    def check_set_limits(self, plot_data_item: "CustomPlotDataItem"):
        if plot_data_item.isVisible():
            self.check_view(plot_data_item)
            self.dataset_visible.check(*plot_data_item.dataset_limits())
        self.dataset_all.check(*plot_data_item.dataset_limits())
        
    def calculate_collection(self, plot_data_container: Dict[str, "CustomPlotDataItem"]):
        idx_vis=0
        idx=0
        for plot_data_item in plot_data_container.values():
            if plot_data_item.isVisible():
                xi_min_view, xi_max_view, yi_min_view, yi_max_view = plot_data_item.view_limits()
                xi_min_data, xi_max_data, yi_min_data, yi_max_data = plot_data_item.dataset_limits()
                if idx_vis == 0:
                    xmin_view, xmax_view, ymin_view, ymax_view = xi_min_view, xi_max_view, yi_min_view, yi_max_view
                    xmin_data_vis, xmax_data_vis, ymin_data_vis, ymax_data_vis = xi_min_data, xi_max_data, yi_min_data, yi_max_data
                    if idx == 0:
                        xmin_data, xmax_data, ymin_data, ymax_data = xi_min_data, xi_max_data, yi_min_data, yi_max_data
                    else:
                        xmin_data, xmax_data, ymin_data, ymax_data = self.get_union_limits(xi_min_data, xi_max_data, yi_min_data, yi_max_data,
                                                                                           xmin_data, xmax_data, ymin_data, ymax_data
                                                                                           )
                    idx_vis+=1
                    continue
                else:
                    xmin_view, xmax_view, ymin_view, ymax_view = self.get_union_limits(xi_min_view, xi_max_view, yi_min_view, yi_max_view,
                                                                                       xmin_view, xmax_view, ymin_view, ymax_view
                                                                                       )
                    xmin_data_vis, xmax_data_vis, ymin_data_vis, ymax_data_vis = self.get_union_limits(xi_min_data, xi_max_data, yi_min_data, yi_max_data,
                                                                                                       xmin_data_vis, xmax_data_vis, ymin_data_vis, ymax_data_vis
                                                                                                       )
            else:
                xi_min_data, xi_max_data, yi_min_data, yi_max_data = plot_data_item.dataset_limits()
                if idx ==0:
                    xmin_data, xmax_data, ymin_data, ymax_data = xi_min_data, xi_max_data, yi_min_data, yi_max_data
                else:
                    xmin_data, xmax_data, ymin_data, ymax_data = self.get_union_limits(xi_min_data, xi_max_data, yi_min_data, yi_max_data,
                                                                                       xmin_data, xmax_data, ymin_data, ymax_data
                                                                                       )        
        self.dataset_view.set(xmin_view, xmax_view, ymin_view, ymax_view)
        self.dataset_visible.set(xmin_data_vis, xmax_data_vis, ymin_data_vis, ymax_data_vis)
        self.dataset_all.set(xmin_data, xmax_data, ymin_data, ymax_data)
        

    def reset_limits(self):
        self.reset_view_limits()
        self.reset_visible_limits()
        self.reset_all_limits()

    def set_axis_view_limit(self, axis, val_min, val_max):
        if axis==0:
            self.dataset_view.xmin=val_min
            self.dataset_view.xmax=val_max
        else:
            self.dataset_view.ymin=val_min
            self.dataset_view.ymax=val_max


    def reset_view_limits(self):
        self.dataset_view.reset()
        
    def reset_visible_limits(self):
        self.dataset_visible.reset()

    def reset_all_limits(self):
        self.dataset_all.reset()

    def view_limits(self):
        return self.dataset_view.xmin, self.dataset_view.xmax, self.dataset_view.ymin, self.dataset_view.ymax
    
    def visible_limits(self):
        return self.dataset_visible.xmin, self.dataset_visible.xmax, self.dataset_visible.ymin, self.dataset_visible.ymax
    
    def all_limits(self):
        return self.dataset_all.xmin, self.dataset_all.xmax, self.dataset_all.ymin, self.dataset_all.ymax

    
    def view_within_bounds(self, axis, lb, ub):
        if axis == 1:
            if self.dataset_view.ymin < lb:
                return False
            if self.dataset_view.ymax > ub:
                return False
        else:
            if self.dataset_view.xmin < lb:
                return False
            if self.dataset_view.xmax > ub:
                return False
        return True

    def set_view_limits(self, xmin, xmax, ymin, ymax):
        if xmin < self.dataset_visible.xmin:
            xmin = self.dataset_visible.xmin
        if xmax > self.dataset_visible.xmax:
            xmax = self.dataset_visible.xmax
        if ymin < self.dataset_visible.ymin:
            ymin = self.dataset_visible.ymin
        if ymax > self.dataset_visible.ymax:
            ymax = self.dataset_visible.ymax

        self.dataset_view.set(xmin, xmax, ymin, ymax)

    def set_dataset_visible_limits(self, xmin, xmax, ymin, ymax):
        self.dataset_visible.set(xmin, xmax, ymin, ymax)
        
    def set_dataset_all_limits(self, xmin, xmax, ymin, ymax):
        self.dataset_all.set(xmin, xmax, ymin, ymax)

    @classmethod 
    def calculate_limits_from_buffer(self, val_min, val_max, buffer):
        dy = buffer * (val_max - val_min)
        return val_min - dy, val_max + dy
    
    
    
    
    
    @classmethod
    def get_union_limits(cls, xi_min, xi_max, yi_min, yi_max, x_min, x_max, y_min, y_max):
        if xi_min < x_min:
            x_min = xi_min
        if xi_max > x_max:
            x_max = xi_max
        if yi_min < y_min:
            y_min = yi_min
        if yi_max > y_max: 
            y_max = yi_max
        return x_min, x_max, y_min, y_max 
                    
