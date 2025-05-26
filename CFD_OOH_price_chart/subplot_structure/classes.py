from __future__ import annotations
from typing import Callable, Sequence, List, Dict, NoReturn, Union, Tuple, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from timeseries.classes import ParentTimeSeries, TimeSeries, TheoTimeSeries
    from instruments.classes import InstrumentContainer, PriceInstrument, SyntheticInstrument
    from managers.classes import SeriesManager
    from ig_measuring.classes import Follower, Leader, WeightMetrics
    
    
from dataclasses import dataclass, field, InitVar
from typing import List, Dict, Tuple
import numpy as np 
import pandas as pd
from mathematics import numerics
from custom_numpy import BufferArray
from mathematics import numerics as math_numerics
from datetime import datetime   
from mathematics.numerics import _METRICS
from custom_qt_classes.plot_data_item import CustomPlotDataItem
from managers.mapping import MappingEngine
import copy
import pyqtgraph as pg
from misc import themes
from timeseries import builders as builders_timeseries
from instruments import classes as classes_instruments
from timeseries import classes as classes_timeseries


@dataclass(slots=True, kw_only=True)
class SubPlotStructure:
    name: str
    instrument_names: List[str]
    mapper: MappingEngine = field(default_factory=lambda: MappingEngine())
    
    focus_instrument: str
    close_point: float
    _current_point: float = field(init=False, default=None)
    metric_attributes: Dict[str, str]
    time_points: List[float] = field(default_factory=dict)
    
    timeseries_parent_container: Dict[str, ParentTimeSeries] = field(default_factory=dict)
    instrument_parent_container: Dict[str, PriceInstrument] = field(default_factory=dict)
    ig_measuring_followers: Dict[str,WeightMetrics] | None = field(default_factory=lambda: None)
    followers: List[str] = field(default_factory=list)
    leaders: Dict[str, Leader] = field(default_factory=dict)
    timeseries_container: Dict[str, TimeSeries] = field(default_factory=dict)
    instruments_container: Dict[str, SyntheticInstrument] = field(default_factory=dict)
    
    def __post_init__(self):
        self.create_init_subsets(self.close_point)
                                
    
    def add_timeseries(self, timeseries: TimeSeries):
        self.timeseries_container[timeseries.name] = timeseries
    
    def create_child_from_expression(self,
                                     instrument_names: List[str] | str,
                                     plot_data_item_container: Dict[str, CustomPlotDataItem],
                                     metric_type_displayed_parent: str,
                                     timestamp: float | None=None,
                                     expression: str | None=None,
                                     ) -> TheoTimeSeries:
        if timestamp is None:
            timestamp = self.close_point
        
        series_parent_container = {}
        
        data_dict_major = {}
        data_dict_minor = {}
        value_attr_parent = "last_y"
        
        for name, plotdataitem in plot_data_item_container.items():
            if name in instrument_names:
                series_parent_container[name] = plotdataitem
                data_dict_major[name] = plotdataitem.dataset_last_values()[-1]
                data_dict_minor[name] = plotdataitem.minor_value
                
        
        specs = self.instrument_parent_container[instrument_names[0]].specs
        info = self.instrument_parent_container[instrument_names[0]].info
        specs_child = classes_instruments.InstrumentSpecs.from_parent(specs,
                                                                                        {"name" : expression}
                                                                                        )
        metric_engine_major = math_numerics.MetricEngine(data_dict_major,
                                                         expression
                                                         )
        metric_engine_minor = math_numerics.MetricEngine(data_dict_minor,
                                                         mode="sum"
                                                         )

        
        kwargs_child = {"name" : expression,
                        "metric_type" : metric_type_displayed_parent,
                        "metric_engine" : metric_engine_major,
                        "metric_engine_minor" : metric_engine_minor,
                        "value_attr_parent" : value_attr_parent,
                        "parent_series_container" : series_parent_container,
                        "parent_minor_metrics" : {self.metric_attributes["minor"] : data_dict_minor}
                        }
        
        timeseries_child = classes_timeseries.TheoTimeSeries.from_plotdataitem_container(series_parent_container,
                                                                                       timestamp,
                                                                                       kwargs_child)
        
        for name, plotdataitem in plot_data_item_container.items():
            if name in instrument_names:
                plotdataitem.add_update_callback(timeseries_child.update)
        
        """
        
        Still deciding on whether it is better to create to a synthetic instrument since the synethic insturment relies on the timeseries, not the other instrument
        
        unique_kwargs_child = {"specs" : specs_child,
                               "info" : info,
                               "basket" : data_dict,
                               "timestamp" : timestamps[-1],
                               "value" : engine.evaluate_scalar(data_dict),
                               ""
                               "value_attr_parent" : {timeseries.name : "get_last_return" for timeseries in self.timeseries_container.values()},
                               "engine" : engine,
                               "metric_type" : value_attr_parent,
                               "metric_calculator" : calculator
                               }

        instrument_child = classes_instruments.SyntheticInstrument(**unique_kwargs_child)
        instrument_child.add_update_callback(timeseries_child.update)
        self.instruments_container[instrument_child.name] = instrument_child
        for name, timeseries in self.timeseries_container.items():
            if name in instrument_names:
                timeseries.add_displayed_dataset_callback(instrument_child.update)
        """
        return timeseries_child

            

    def create_subsets(self, timestamp: float):
        if self._current_point is None or self._current_point > timestamp:
            if isinstance(self.metric_attributes["value_attr_parent"], list):
                value_attr_parent = "value"
            else:
                value_attr_parent = "value"
            for name, timeseries_child in self.timeseries_container.items():
                
                timeseries_parent = self.timeseries_parent_container[name]
                
                dummy_timeseries_child = timeseries_parent.create_child(start_time=timestamp,
                                                                        end_time=np.amax(timeseries_parent.timestamps),
                                                                        metric_type="mid", 
                                                                        metric_type_displayed_child=self.metric_attributes["metric_type_displayed_child"], 
                                                                        value_attr_parent=value_attr_parent,
                                                                        inclusion_flags=True
                                                                        )
                
                timestamps, values = dummy_timeseries_child.get_data()
                timeseries_child = timeseries_child.set_data(timestamps, values)
                
            create_new_flag=False
        else:
            for name, timeseries_child in self.timeseries_container.items():
                timeseries_child.subset(timestamp)                
            create_new_flag=False
        self._current_point=timestamp
        return create_new_flag   

    def create_init_subsets(self, timestamp: float):
        for name, timeseries_parent in self.timeseries_parent_container.items():
            instrument_parent = self.instrument_parent_container[name]
            timeseries_child = timeseries_parent.create_child(start_time=timestamp,
                                                              end_time=np.amax(timeseries_parent.timestamps),
                                                              metric_type=self.metric_attributes["major"], 
                                                              scale=self.metric_attributes["scale"],
                                                              value_attr_parent=self.metric_attributes["value_attr_parent"],
                                                             )
            if name in self.timeseries_container:
                old_timeseries = self.timeseries_container[name]
                instrument_parent.remove_update_callback(old_timeseries.update)

            
            instrument_parent.add_update_callback(timeseries_child.update)
            
            
            timeseries_child.parent_minor_metrics={self.metric_attributes["minor"] : None}
            timeseries_child.add_metric_callback(self.metric_attributes["minor"])
            
            self.add_timeseries(timeseries_child)
        self._current_point=timestamp
        
    def reset_timeseries(self):
        return self.create_subsets(self.close_point)
        

    def clone(self):
        timeseries_copy = {}
        colours = themes.get_colours()
        for idx, (name, timeseries) in enumerate(self.timeseries_container.items()):
            timeseries_new = timeseries.clone_without_callbacks()
            colour = colours[idx]
            plot_data_item = CustomPlotDataItem(timeseries=timeseries,
                                                name=name,
                                                pen=pg.mkPen(color=colour),
                                                width=1,
                                                color=colour
                                                )
            timeseries_new.add_update_callback(plot_data_item.update_from_timeseries_update)
            timeseries_copy[name] = timeseries_new
        return SubPlotStructure(name=self.name,
                                instrument_names=self.instrument_names.copy(),
                                mapper=copy.deepcopy(self.mapper),
                                focus_instrument=self.focus_instrument,
                                close_point=self.close_point,
                                metric_attributes=self.metric_attributes.copy(),
                                time_points=self.time_points.copy(),
                                timeseries_container=timeseries_copy
                                )
    def clone_without_timeseries(self):
        return SubPlotStructure(name=self.name,
                                instrument_names=self.instrument_names.copy(),
                                mapper=copy.deepcopy(self.mapper),
                                focus_instrument=self.focus_instrument,
                                close_point=self.close_point,
                                metric_attributes=self.metric_attributes.copy(),
                                time_points=self.time_points.copy(),
                                )