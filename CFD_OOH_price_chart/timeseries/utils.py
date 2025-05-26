from __future__ import annotations
from typing import List, Dict
import pandas as pd
from custom_numpy import BufferArray
from .classes import TimeSeries
from plot_config.classes import SubPlotStructure

"""

def create_all_parent_timeseries(instrument_names: List[str], data_all: Dict[str, pd.DataFrame]):
    time_series_containers={}
    for instrument_name in instrument_names:
        df = data_all[instrument_name]
        time_series_containers[instrument_name] = _create_parent_timeseries(instrument_name, df)
    return time_series_containers
    
def _create_parent_timeseries(instrument_name: str, data: pd.DataFrame):
    kwargs = {"name" : instrument_name,
              "timestamp" : data.index.tolist(),
              "bid" : data["bid"].values.tolist(),
              "ask" : data["ask"].values.tolist(),
              "mid" : data["mid"].values.tolist()
            }
    return ParentTimeSeries(**kwargs)

def init_percent_timeseries(parent_timeseries_all: Dict[str, ParentTimeSeries], plot_config_structure: Dict[str, PlotConfig]):
    for plot_name, plot_config in plot_config_structure.items():
        

        for instrument_name in plot_config.instrument_names:
            parent_timeseries = parent_timeseries_all[instrument_name]
            close_ts = plot_config.close_point
            subset_timeseries = parent_timeseries.create_subset(close_ts, "mid")
            S_0 = subset_timeseries.value.get_array()[0]
            
            subset_timeseries.value = 100 * (subset_timeseries.value / S_0 - 1) 
            plot_config.add_timeseries("subset", subset_timeseries, close_ts)



"""





def create_theo_time_series(operation_exp, instrument_list, time_series_dict):
    instruments_in_operation=[] 
    data_tuples=[]
    value_dict={}
    for instrument_name in instrument_list:
        if instrument_name in operation_exp:
            instruments_in_operation.append(instrument_name)
            timestamps, values = time_series_dict[instrument_name].get_data()
            data_tuples.append((instrument_name, timestamps, values))
            value_dict[instrument_name] = values[-1]
    
    timestamps, value_array_dict = utils.concat_data_tuples(data_tuples)
    
    engine=utils.CustomOperation(value_dict, operation_exp)
    
    value = engine.compiler(value_array_dict)
    
    timestamp = BufferArray(True, False, "timestamp", timestamps)
    value = BufferArray(True, False, "value", value)
    
    parent_timestamps = ParentArray(value=timestamp, variable_name="timestamp")
    parent_values = ParentArray(value=value, variable_name="value")
    theo_time_series = TimeSeriesSingle(name=operation_exp,
                                        timestamp=parent_timestamps,
                                        value=parent_values)
    return theo_time_series, engine

def init_theo_time_series(percent_time_series_dict: Dict[str, Dict[str, Dict[float, TimeSeriesSinglePerc]]], region_dataclasses: Dict[str, Region], market_maps):
    theo_time_series_dict = {}
    engine_dict={}
    for plot_name, market_map in market_maps.items():
        default_operations = market_map["default_operations"]
        ts = region_dataclasses[plot_name].close_ts
        instrument_list = region_dataclasses[plot_name].instrument_names
        inner_theo_time_series_dict={}
        inner_engine_dict={}
        for default_operation in default_operations:
            time_series_dict={name : time_series[ts] for name, time_series in percent_time_series_dict[plot_name].items()}
            theo_time_series, engine = create_theo_time_series(default_operation, instrument_list, time_series_dict)
            inner_engine_dict[default_operation]=engine
            inner_theo_time_series_dict[default_operation] = theo_time_series
        theo_time_series_dict[plot_name] = inner_theo_time_series_dict
        engine_dict[plot_name] = inner_engine_dict
        
    return theo_time_series_dict, engine_dict
