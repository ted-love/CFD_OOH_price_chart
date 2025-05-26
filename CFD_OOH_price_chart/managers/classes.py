from __future__ import annotations
from typing import List, Dict, Union, Tuple, Callable, TYPE_CHECKING, ClassVar
if TYPE_CHECKING:
    from instruments.classes import PriceInstrument, SyntheticInstrument, PriceInstrument, PriceInstrumentSnapshot, SyntheticInstrumentSnapshot, BaseInstrumentSnapshot
    from timeseries.classes import TimeSeries
    from mathematics.numerics import MetricEngine
    from .classes import SubPlotStructure, SeriesManager

from dataclasses import dataclass, field, InitVar
from datetime import datetime   
from mathematics.numerics import _METRICS
from mathematics import numerics as math_numerics
from instruments import classes as classes_instruments
from timeseries import classes as classes_timeseries
from timeseries import builders as builders_timeseries
import custom_numpy

@dataclass(slots=True)
class GlobalMap:
    series_managers: InitVar[List[SeriesManager]]
    
    base_name_internal: Dict[str, float] = field(default_factory=dict)
    child_parent_internal: Dict[str, Dict[float, str]] = field(default_factory=dict)
    ts_metric_internal: Dict[float, Dict[str, float]] = field(default_factory=dict)
    metric_ts_internal: Dict[float, Dict[str, float]] = field(default_factory=dict)
    
    def __post_init__(self, series_manager: SeriesManager):
        for series_manager in series_manager:
            self.base_name_internal[series_manager.name] = series_manager.internal_name
            self.ts_metric_internal[series_manager.timestamp_filters] = {series_manager.metric_type : series_manager.internal_name}
            self.metric_ts_internal[series_manager.metric_type] = {series_manager.timestamp_filters : series_manager.internal_name}


    def create_id_info(self,
                       name: str,
                       metric_type: str,
                       timestamp: str,
                       parent_internal_name: float,
                       ) -> Tuple[str, str]:
        internal_name = datetime.now().timestamp()
        identifier = f"{name}_{metric_type}"
        self.update(internal_name, identifier, name, timestamp, parent_internal_name)
        return internal_name, identifier
    
    def update_from_series_manager(self,
                                   manager_child: SeriesManager,
                                   manager_parent: SeriesManager):
        self.update(manager_child.internal_name,
                    manager_child.metric_type,
                    manager_child.name,
                    manager_child.timestamp_filters,
                    manager_parent.internal_name
                    )
    
    
    def update(self, internal_name, metric_type, name, timestamp, parent_internal_name):
        #self.ts_id_internal[timestamp][identifier] = internal_name
        #self.id_ts_internal[identifier][timestamp] = internal_name
        self.child_parent_internal[internal_name] = parent_internal_name
        self.ts_metric_internal[timestamp][metric_type] = internal_name
        
        
    def get_base_internal_name(self,
                               name
                               ):
        return self.base_name_internal[name]
        
            
            
@dataclass(slots=True)
class GlobalInstrumentManager:
    base_series_managers: InitVar[List[SeriesManager]]
    all_series_managers: Dict[float, SeriesManager] = field(default_factory=dict)
    mapper: GlobalMap = field(default=None)
    
    
    
    def __post_init__(self, base_series_managers: List[SeriesManager]):
        self.mapper = GlobalMap(base_series_managers)
        for series_manager in base_series_managers:
            self.all_series_managers[series_manager.internal_name] = series_manager
        


    def create_returns(self,
                       series_manager_parent: SeriesManager,
                       timestamp: float,
                       returns_type: str,
                       price_attr_parent: str,
                        ) -> SeriesManager:
        
        
        parent_snapshot = series_manager_parent.create_snapshot_instrument(timestamp)


        total_parent_instruments = [series_manager_parent.instrument, series_manager_parent.snapshot_instrument_parent]
        parent_timeseries = series_manager_parent.timeseries
        
        data_dict = {}
        for instrument_object in total_parent_instruments:
            data_dict[instrument_object.identifier] = getattr(instrument_object, price_attr_parent)
                
        engine = math_numerics.MetricEngine(data_dict)
        
        child_timeseries = parent_timeseries.create_child_at_idx(parent_snapshot.idx_timeseries,
                                                                 price_attr_parent=price_attr_parent,
                                                                 kwargs_for_child={"metric_type" : returns_type}
                                                                 )
        
        child_timeseries.values = engine.evaluate_array(child_timeseries.get_values())

        unique_kwargs_child = {
                                "basket" : data_dict,
                                "value" : child_timeseries.values[-1],
                                "price_attr_parent" : {series_manager_parent.instrument.identifier | price_attr_parent},
                                "engine" : engine,
                                "metric_type" : returns_type
                            }
        child_instrument = series_manager_parent.instrument.create_child("SyntheticInstrument",
                                                                          unique_kwargs_child)

        series_manager_child = SeriesManager.create_from_objects(child_objects=[child_timeseries, child_instrument],
                                                                 timestamp_filters=timestamp,
                                                                 snapshot_instrument_parent=parent_snapshot)
        self.mapper.update_from_series_manager(series_manager_child, series_manager_parent)
        return series_manager_child



@dataclass(slots=True, kw_only=True)
class SeriesManager:
    name: str = field(default=None)
    metric_type: str = field(default=None)
    timeseries: TimeSeries | None
    instrument: PriceInstrument | SyntheticInstrument
    timestamp_filters: float | Tuple[float] = field(default=None)
    snapshot_instrument_parent: PriceInstrumentSnapshot | SyntheticInstrumentSnapshot = field(default=None)
    internal_name: float = field(default_factory=lambda: datetime.now().timestamp())
    identifier: str = field(default=None)
    engine: MetricEngine | None = field(default=None)
    
    def create_snapshot_instrument(self,
                                   timestamp_filter: float
                                   ) -> PriceInstrumentSnapshot | SyntheticInstrumentSnapshot:
        
        
        instrument_snapshot = classes_instruments.BaseInstrumentSnapshot.from_timeseries(self.instrument,
                                                                                         self.timeseries,
                                                                                         timestamp_filter,
                                                                                         True,)
        return instrument_snapshot
    
    
    @classmethod
    def from_multi_parent(cls,
                          series_managers: List[SeriesManager],
                          metric_type: str,
                          timestamp: float,
                          expression: str,
                          chart_name: str
                          ):
        data_dict = {}
        timestamp_filters = series_managers[0].timestamp_filters
        specifications = series_managers[0].instrument.specs
        info = series_managers[0].instrument.info
        
        for manager in series_managers:
            data_dict[manager.identifier] = manager.instrument.value
        
        engine = math_numerics.MetricEngine(data_dict,
                                            expression
                                            )
        
        if len(series_managers) == 2:
            display_name = expression
        else:
            display_name = f"theo_{chart_name}"

        timestamps, series_dict = builders_timeseries.concat_timeseries({manager.identifier : manager.timeseries for manager in series_managers})
        
        
        timeseries_values = engine.evaluate_array(series_dict)
        
        timeseries_child = classes_timeseries.TimeSeries(name=expression,
                                                         metric_type=metric_type,
                                                         timestamps=custom_numpy.BufferArray(timestamps),
                                                         values=custom_numpy.BufferArray(timeseries_values),
                                                         )
        
        specifications_child = classes_instruments.InstrumentSpecs.from_parent(specifications,
                                                                                        {"name" : expression})
        
        unique_kwargs_child = {"specifications" : specifications_child,
                               "info" : info,
                               "display_name" : display_name,
                               "basket" : data_dict,
                               "timestamp" : timestamps[-1],
                               "value" : engine.__call__(data_dict),
                               "price_attr_parent" : {manager.identifier : "value" for manager in series_managers},
                               "engine" : engine,
                               "metric_type" : metric_type}
        
        instrument_child = classes_instruments.SyntheticInstrument(**unique_kwargs_child)
        instrument_child.add_update_callback(timeseries_child.update)
        
        for parent_manager in series_managers:
            parent_manager.instrument.add_update_callback(instrument_child.update)
        
        
        
        return cls(name=expression, metric_type=metric_type, timeseries=timeseries_child, instrument=instrument_child, timestamp_filters=timestamp_filters, engine=engine,)

    
    @classmethod
    def create_from_objects(cls,
                            child_objects: List[TimeSeries | PriceInstrument | SyntheticInstrument],
                            metric_type: str,
                            timestamp_filters: float | Tuple[float] = None,
                            ) -> SeriesManager:
        kwargs = {"timestamp_filters" : timestamp_filters,
                  "metric_type" : metric_type,
                  "identifier" : f"{child_objects[0].name}_{metric_type}"
                  }
        
        for child in child_objects:
            if isinstance(child,  (classes_instruments.PriceInstrument, classes_instruments.SyntheticInstrument)):
                kwargs["name"] = child.name
                kwargs["metric_type"] = child.metric_type
                kwargs["instrument"] = child
                
            if isinstance(child,  (classes_timeseries.TimeSeries | classes_timeseries.ParentTimeSeries)):
                kwargs["timeseries"] = child
            
            if isinstance(child,  (classes_instruments.BaseInstrumentSnapshot)):
                kwargs["snapshot_instrument_parent"] = child

        return cls(**kwargs)
    
    @classmethod
    def from_parent_manager_old(cls,
                            other_series_manager: PriceInstrument,
                            subplot_kwargs,
                            args_create_child_timeseries,
                            kwargs_create_child_timeseries,
                            args_create_child_instrument,
                            kwargs_create_child_instrument
                            ) -> PriceInstrument:
        
        
        if (other_series_manager.metric_type == "price"
            and subplot_kwargs["metric_type"] != "price"
            and not hasattr(other_series_manager.timeseries, subplot_kwargs["price_type"])):
            
            parent_instrument, parent_timeseries = other_series_manager.instrument, other_series_manager.timeseries
            proxy_child_instrument, proxy_timeseries = cls.create_proxy_series(subplot_kwargs, parent_instrument, parent_timeseries)

        else:
            proxy_child_instrument = other_series_manager.instrument.create_child()
            proxy_child_instrument, proxy_timeseries = other_series_manager.instrument, other_series_manager.timeseries
        
        child_instrument = proxy_child_instrument.create_child(*args_create_child_instrument, kwargs_create_child_instrument)
        
        child_timeseries = proxy_timeseries.create_child(*args_create_child_timeseries, **kwargs_create_child_timeseries)
        
        series_values = child_instrument.evaluate_series(child_timeseries.values.get_array())
        
        child_timeseries.values = series_values.values
        
        return cls(base=False,
                metric_type=subplot_kwargs["metric_type"],
                   timeseries=series_values,
                   instrument=child_instrument,
                   )

    @classmethod
    def from_parent(self,
                    series_manager_parent: SeriesManager,
                    timestamp: float,
                    metric_type: str,
                    price_attr_parent: str,
                    ) -> SeriesManager:
        
        
        parent_snapshot = series_manager_parent.create_snapshot_instrument(timestamp)
        total_parent_instruments = [series_manager_parent.instrument, parent_snapshot]
        parent_timeseries = series_manager_parent.timeseries
        
        data_dict = {}
        for instrument_object in total_parent_instruments:  
            data_dict[instrument_object.identifier] = instrument_object.get_value_kwargs(price_attr_parent)
        
        engine = math_numerics.MetricEngine(data_dict, metric=metric_type)
        child_timeseries = parent_timeseries.create_child_at_idx(parent_snapshot.idx_timeseries,
                                                                 price_attr_parent=price_attr_parent,
                                                                 kwargs_for_child={"metric_type" : metric_type}
                                                                 )
        data_dict_timeseries = {}
        for identifier in data_dict:
            if identifier == parent_snapshot.identifier:
                data_dict_timeseries[identifier] = data_dict[identifier]
            else:
                data_dict_timeseries[identifier] = child_timeseries.values
        
        

        child_timeseries.values = engine.evaluate_array(data_dict_timeseries)
     
        unique_kwargs_child = {
                            "basket" : data_dict,
                            "value" : child_timeseries.values[-1],
                            "price_attr_parent" : {series_manager_parent.instrument.identifier : price_attr_parent},
                            "engine" : engine,
                            "metric_type" : metric_type}
        
        child_instrument = series_manager_parent.instrument.create_child("SyntheticInstrument",
                                                                         unique_kwargs_child)
        child_instrument.add_update_callback(child_timeseries.update)
        
        print(f"\n\nbefore filter: {timestamp}\n\n")
        series_manager_child = SeriesManager.create_from_objects(child_objects=[child_timeseries, child_instrument, parent_snapshot],
                                                                 metric_type=metric_type,
                                                                 timestamp_filters=timestamp)
        return series_manager_child


            