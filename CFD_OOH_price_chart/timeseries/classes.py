from __future__ import annotations
from typing import List, Dict, Union, Tuple, Callable, TYPE_CHECKING, Any
if TYPE_CHECKING:
    from instruments.classes import PriceInstrument, SyntheticInstrument
    from mathematics.numerics import MetricEngine, MetricConverter
    from custom_qt_classes.view_box import CustomViewBox
    from custom_qt_classes.plot_data_item import CustomPlotDataItem
    from custom_qt_classes.data_helpers import SeriesContainer

from dataclasses import dataclass, field, InitVar
import bottleneck
import numpy as np
from custom_numpy import BufferArray
from itertools import permutations
from datetime import datetime
from abc import ABC, abstractmethod
from mathematics import numerics as math_numerics


@dataclass(slots=True, kw_only=True)
class _BaseTimeSeries(ABC):
    name: str
    metric_type: str | List[str]
    timestamps: List[float] | BufferArray | np.ndarray
    _update_callbacks: List[Callable] = field(default_factory=lambda: [])
    
    def update_cleanup(self):
        for callback in self._update_callbacks:
            callback(self)

    @staticmethod
    def find_idx_filters(x: BufferArray|np.ndarray|List,
                         x_lb: float, 
                         x_ub: float,
                         ) -> Tuple[BufferArray, BufferArray]:
        return np.searchsorted(x, x_lb, side="right") - 1, np.searchsorted(x, x_ub, side="left")

    def add_update_callback(self, callback: Callable) -> None:
        self._update_callbacks.append(callback)
    
    def remove_update_callback(self, callback: Callable) -> None:
        self._update_callbacks.remove(callback)

    @abstractmethod
    def update(self, instrument: PriceInstrument | SyntheticInstrument):
        ...
        

@dataclass(slots=True, kw_only=True)
class ParentTimeSeries(_BaseTimeSeries):
    metric_type: List[str] = field(default_factory=lambda: ["bid", "ask", "mid"])
    bid: List[float] = field(default_factory=list)
    ask: List[float] = field(default_factory=list)

    def update(self, instrument: PriceInstrument):
        self.timestamps.append(instrument.timestamp)
        self.bid.append(instrument.bid)
        self.ask.append(instrument.ask) 
        self.update_cleanup()

    def create_child_at_idx(self,
                            idx_1: int=None,
                            idx_2: int=None,
                            metric_type: str|None=None,
                            scale: str | None=None,
                            value_attr_parent: List[str]|str=None,
                            metric_engine: MetricConverter | MetricEngine=None,
                            ) -> TimeSeries:
        if idx_1 is None:
            idx_1 = 0
        if idx_2 is None:
            idx_2 = len(self.timestamps)
        
        timestamps = np.array(self.timestamps[idx_1:idx_2])
        if value_attr_parent == "mid":
            convert_values_arg = (self.bid[idx_1:idx_2], self.ask[idx_1:idx_2])
        else:
            convert_values_arg = getattr(self, value_attr_parent)[idx_1:idx_2]   
        if metric_engine is None:
            metric_engine = math_numerics.MetricConverter(values=convert_values_arg,
                                                          metric=metric_type,
                                                          scale=scale,
                                                          )
        
        values = metric_engine.base(*convert_values_arg)

        if isinstance(value_attr_parent, list):
            value_attr_parent_converter = "value"
        else:
            value_attr_parent_converter = "value"
        kwargs = {"name" : self.name,
                  "metric_type" : metric_type,
                  "value_attr_parent" : value_attr_parent_converter,
                  "timestamps" : BufferArray(timestamps),
                  "values" : BufferArray(values),
                  "metric_engine" : metric_engine,
                  }
        return TimeSeries(**kwargs)
        
    def create_child(self,
                     start_time: float | None=None,
                     end_time: Union[float, None]=None,
                     metric_type: str | None=None,
                     scale: str | None=None,
                     value_attr_parent: str | None=None,
                     ) -> TimeSeries:
        idx_1, idx_2 = self.find_idx_filters(self.timestamps,
                                             start_time,
                                             end_time,
                                             )
        if idx_1 == len(self.timestamps)-1:
            idx_1 = len(self.timestamps) - 3
        return self.create_child_at_idx(idx_1,
                                        idx_2,
                                        metric_type,
                                        scale,
                                        value_attr_parent
                                        )

        
@dataclass(slots=True, kw_only=True)
class TimeSeries(_BaseTimeSeries):
    value_attr_parent: str
    metric_engine: MetricEngine|MetricConverter
    metric_engine_minor: MetricEngine|MetricConverter = field(default_factory=lambda: None)
    
    timestamps: BufferArray[float] = field(default_factory=lambda: None)
    values: BufferArray[float] = field(default_factory=lambda: None)
    parent_minor_metrics: Dict[str, float] | None = field(default_factory=lambda: {})
    idx_lb: int = field(default_factory=lambda: 0)
    idx_ub: int = field(default_factory=lambda: 1)
    update_displayed_dataset_callbacks: List[Callable] = field(default_factory=lambda: [])
    changed_dataset_series_callbacks: List[Callable] = field(default_factory=lambda: [])
    metric_callbacks: List[str] = field(default_factory=lambda: [])
    
    def __post_init__(self):
        self.idx_ub=self.values.n
        
    def update(self, instrument: PriceInstrument | SyntheticInstrument):
        self.timestamps.append(instrument.timestamp)
        self.values.append(self.metric_engine.base(*getattr(instrument, self.value_attr_parent)))
        self.get_parent_metrics(instrument)
        self.update_cleanup()
    
    def get_parent_metrics(self, instrument: PriceInstrument | SyntheticInstrument):
        for metric_name in self.metric_callbacks:
            self.parent_minor_metrics[metric_name] = getattr(instrument, self.value_attr_parent)
    
    def add_metric_callback(self,
                            metric_name: str,
                            ):
        self.metric_callbacks.append(metric_name)
        

    def get_values(self):
        return self.values.get_array()
    
    def get_timestamps(self):
        return self.timestamps.get_array()
    
    def get_last_value(self):
        return self.values.get_last_value() 
    
    def get_last_timestamp(self):
        return self.timestamps.get_last_value() 
    
    def set_data(self, timestamps, values):
        self.timestamps = BufferArray(timestamps)
        self.values = BufferArray(values)
    
    def get_data(self):
        return self.timestamps.get_array(), self.values.get_array()    
    
    def subset(self, timestamp):
        idx_1, idx_2, = self.find_idx_filters(True, timestamp)
        timestamps, values = self.get_data()
        ts_filt = timestamps[idx_1:idx_2]
        val_filt = values[idx_1:idx_2]
        self.timestamps = BufferArray(ts_filt)
        self.values = BufferArray(val_filt)
        self.update_cleanup()
        

    def create_child_at_idx(self,
                            idx_1: int=None,
                            idx_2: int=None,
                            metric_type_child: str | None=None,
                            metric_type_displayed_child: str | None=None,
                            value_attr_parent: str | None=None,
                            metric_engine: MetricEngine | None=None,
                            ) -> TimeSeries:
        if idx_1 is None:
            idx_1 = 0
        if idx_2 is None:
            idx_2 = len(self.timestamps)

        timestamps = np.array(self.timestamps[idx_1:idx_2])
        
        if metric_type_child is None:
            metric_type_child=self.metric_type

        if metric_engine is None:
            metric_engine = math_numerics.MetricConverter(metric=metric_type_child,
                                                          metric_parent=value_attr_parent,
                                                          scale=None
                                                          )
        values = metric_engine(getattr(self, value_attr_parent)[idx_1:idx_2])

        metric_engine_display = math_numerics.MetricConverter(self.name,
                                                            values,
                                                            metric_type_displayed_child,
                                                            self.metric_type)

        kwargs = {"name" : self.name,
                  "metric_type" : metric_type_child,
                  "metric_type_displayed_child" : metric_type_displayed_child,
                  "value_attr_parent" : value_attr_parent,
                  "timestamps" : BufferArray(timestamps),
                  "values" : BufferArray(values),
                  "metric_engine" : metric_engine,
                  "metric_engine_display":metric_engine_display
                  }
        return TimeSeries(**kwargs)

    def clone_without_callbacks(self) -> TimeSeries:
        return TimeSeries(name=self.name,
                          metric_type=self.metric_type,
                          value_attr_parent=self.value_attr_parent, 
                          timestamps=BufferArray(np.copy(self.timestamps)),
                          values=BufferArray(np.copy(self.values)),
                          metric_engine=self.metric_engine,
                          )
    
    
        
@dataclass(slots=True, kw_only=True)
class TheoTimeSeries(TimeSeries):
    parent_series_container: Dict[str, CustomPlotDataItem] = field(default_factory=dict) 
    values_expanded_parent_container: Dict[str, np.ndarray] = field(default_factory=dict)  # This is data expanded to the union timestamps without forward-fill
    idx_parent_container: Dict[str, np.ndarray] = field(default_factory=dict)
    idx_lb_parent_container: Dict[str, np.ndarray] = field(default_factory=dict)
    
    def __post_init__(self):
        super(TheoTimeSeries, self).__post_init__()

        
    def update(self, parent: CustomPlotDataItem):
        timestamp, value = parent.dataset_last_values()
        last_ts = self.get_last_timestamp()
        if timestamp < last_ts:
            timestamp = last_ts + 1e-3
        self.timestamps.append(timestamp)
        self.values.append(self.metric_engine({parent.name() : value}))
        
        for name, expanded_parent in self.values_expanded_parent_container.items():
            if name == parent.name():
                self.values_expanded_parent_container[name] = np.append(expanded_parent, value)
                self.idx_parent_container[name] = np.append(self.idx_parent_container[parent.name()], self.values_expanded_parent_container[name].size-1)
            else:
                self.values_expanded_parent_container[name] = np.append(expanded_parent, np.nan)
                
        self.get_parent_metrics(parent)
        self.update_cleanup()
        
    def get_parent_metrics(self, parent: CustomPlotDataItem):
        for metric_name in self.metric_callbacks:
            self.parent_minor_metrics[parent.metric_minor][parent.name()] = parent.minor_value

    def evaluate_timeseries_on_view(self):
        new_value_dict={}
        for name, plotdataitem in self.parent_series_container.items():
            _, values = plotdataitem.view_set()
            idx = self.idx_parent_container[name]
            idx = idx[-values.size:]
            self.values_expanded_parent_container[name][idx] = values
            ffill_vals = bottleneck.push(self.values_expanded_parent_container[name])
            
            new_value_dict[name] = ffill_vals[self.idx_lb:]            
            self.metric_engine.update_data_dict(values[-1], name)
        self.values = BufferArray(self.metric_engine.evaluate_array(new_value_dict))
        
    def update_displayed_dataset_bounds(self,
                                        view_box: CustomViewBox,
                                        x_bounds: List[float, float]
                                        ) -> None:        
        self.idx_lb, self.idx_ub, self.find_idx_filters(self.get_timestamps(), *x_bounds)
        self.evaluate_timeseries_on_view()
    
    @classmethod
    def _from_container(cls,
                        container: Dict[str, TimeSeries|TheoTimeSeries|CustomPlotDataItem],
                        timestamp: float, 
                        data_call: Callable,
                        kwargs_child: Dict[str, Any]
                        ) -> TheoTimeSeries:
        idx_container={}
        values_expanded_parent_container = {}
        _ffill_values_expanded_parent_container={}
        idx_lb_container={}
        
        ts_combined = np.array([])
        for name_parent, series_parent in container.items():
            ts, _ = getattr(series_parent, data_call)()
            ts_combined = np.append(ts_combined, ts)
        ts_combined = np.unique(ts_combined)
        ts_idx_lb = np.searchsorted(ts_combined, timestamp)
        ts_idx_lb=0
        for name_parent, series_parent in container.items():
            ts, _ = getattr(series_parent, data_call)()
            idx = np.searchsorted(ts_combined, ts)
            idx_container[name_parent] = idx
            values_expanded = np.full_like(ts_combined, np.nan)
            _, parent_values = getattr(series_parent, data_call)()
            
            values_expanded[idx] = parent_values

            values_expanded_parent_container[name_parent] = values_expanded
            _ffill_values_expanded_parent_container[name_parent] = bottleneck.push(values_expanded)

            ts_expanded = bottleneck.push(np.full_like(ts_combined, np.nan))
            idx_lb_container[name_parent] = np.searchsorted(ts_expanded, timestamp, side="left")
            
        metric_engine =kwargs_child["metric_engine"]
        values_child = metric_engine.evaluate_array(_ffill_values_expanded_parent_container)

        kwargs_child["timestamps"] = BufferArray(ts_combined)
        kwargs_child["values"] = BufferArray(values_child)
        kwargs_child["idx_lb"] = ts_idx_lb
        kwargs_child["values_expanded_parent_container"]=values_expanded_parent_container
        kwargs_child["idx_lb_parent_container"] = idx_lb_container
        kwargs_child["idx_parent_container"]=idx_container
        return cls(**kwargs_child)

    
    @classmethod
    def from_plotdataitem_container(cls,
                                    plotdataitem_container: Dict[str, TimeSeries|TheoTimeSeries],
                                    timestamp: float, 
                                    kwargs_child: Dict[str, Any]
                                    ) -> TheoTimeSeries:
        return TheoTimeSeries._from_container(plotdataitem_container,
                                              timestamp,
                                              "dataset",
                                              kwargs_child
                                              )
        
    
    @classmethod
    def from_timeseries_container(cls,
                                  timeseries_container: Dict[str, TimeSeries|TheoTimeSeries],
                                  timestamp: float, 
                                  kwargs_child: Dict[str, Any]
                                  ) -> TheoTimeSeries:
        return TheoTimeSeries._from_container(timeseries_container,
                                              timestamp,
                                              "get_data",
                                              kwargs_child
                                              )













































@dataclass(slots=True, kw_only=True)
class TheoTimeSeries22222222222(TimeSeries):
    timeseries_parent_container: Dict[str, TimeSeries] = field(default_factory=dict) 
    values_expanded_parent_container: Dict[str, np.ndarray] = field(default_factory=dict)  # This is data expanded to the union timestamps without forward-fill
    idx_parent_container: Dict[str, np.ndarray] = field(default_factory=dict)
    idx_lb_parent_container:Dict[str, np.ndarray] = field(default_factory=dict)
    
    def __post_init__(self):
        super(TheoTimeSeries, self).__post_init__()

        
    def update(self, parent: CustomPlotDataItem):
        timestamp, value = parent.dataset_last_values()
        self.timestamps.append(timestamp)
        self.values.append(self.metric_engine({parent.name() : value}))
        
        for name, expanded_parent in self.values_expanded_parent_container.items():
            if name == parent.name:
                self.values_expanded_parent_container[name] = np.append(expanded_parent, getattr(parent, self.value_attr_parent))
                self.idx_parent_container[name] = np.append(self.idx_parent_container[parent.name], self.values_expanded_parent_container[name].size-1)
            else:
                self.values_expanded_parent_container[name] = np.append(expanded_parent, np.nan)
                
        self.update_cleanup()
        

    def evaluate_timeseries(self):
        new_value_dict={}
        for name, timeseries in self.timeseries_parent_container.items():
            values = timeseries.get_values()
            idx = idx[-values.size:]
            self.values_expanded_parent_container[name][idx] = values
            ffill_vals = bottleneck.push(self.values_expanded_parent_container[name])
            
            new_value_dict[name] = ffill_vals[self.idx_lb:]            
            self.metric_engine.update_data_dict(values[-1], name)
        
        self.values = BufferArray(self.metric_engine.evaluate_array(new_value_dict))
        self._displayed_dataset[1]=self.metric_engine_display(BufferArray(self.metric_engine.evaluate_array(new_value_dict)))
        
    def update_displayed_dataset_bounds(self,
                                        view_box: CustomViewBox,
                                        x_bounds: List[float, float]
                                        ) -> None:
        
        self._filter_for_display=True
        
        self.idx_lb, self.idx_ub, self.find_idx_filters(self._displayed_dataset[0], *x_bounds)
        self.evaluate_timeseries()
    
    @classmethod
    def from_timeseries_container(cls,
                                  timeseries_container: Dict[str, TimeSeries|TheoTimeSeries],
                                  timestamp: float, 
                                  kwargs_child: Dict[str, Any]
                                  ) -> TheoTimeSeries:
        idx_container={}
        values_expanded_parent_container = {}
        _ffill_values_expanded_parent_container={}
        idx_lb_container={}
        
        ts_combined = np.array([])
        for name_parent, timeseries_parent in timeseries_container.items():
            ts = timeseries_parent.get_timestamps()
            ts_combined = np.append(ts_combined, ts)
        ts_combined = np.unique(ts_combined)
        ts_idx_lb = np.searchsorted(ts_combined, timestamp)
        ts_idx_lb=0
        for name_parent, timeseries_parent in timeseries_container.items():
            idx = np.searchsorted(ts_combined, timeseries_parent.get_timestamps())
            idx_container[name_parent] = idx
            values_expanded = np.full_like(ts_combined, np.nan)
            parent_values = timeseries_parent.get_values()
            
            values_expanded[idx] = parent_values

            values_expanded_parent_container[name_parent] = values_expanded
            _ffill_values_expanded_parent_container[name_parent] = bottleneck.push(values_expanded)

            ts_expanded = bottleneck.push(np.full_like(ts_combined, np.nan))
            idx_lb_container[name_parent] = np.searchsorted(ts_expanded, timestamp, side="left")
            
        metric_engine =kwargs_child["metric_engine"]
        print(_ffill_values_expanded_parent_container)
        values_child = metric_engine.evaluate_array(_ffill_values_expanded_parent_container)

        kwargs_child["timestamps"] = BufferArray(ts_combined)
        kwargs_child["values"] = BufferArray(values_child)
        kwargs_child["idx_lb"] = ts_idx_lb
        kwargs_child["values_expanded_parent_container"]=values_expanded_parent_container
        kwargs_child["idx_lb_parent_container"] = idx_lb_container
        kwargs_child["idx_parent_container"]=idx_container
        return cls(**kwargs_child)
