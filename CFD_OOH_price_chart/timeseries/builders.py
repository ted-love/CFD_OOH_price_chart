from __future__ import annotations
from typing import List, Dict, TYPE_CHECKING, Tuple
if TYPE_CHECKING:
    from timeseries.classes import TimeSeries
    
    
import pandas as pd
from . import classes as classes_timeseries
import numpy as np

def create_parent_timeseries_container(data_all: Dict[str, pd.DataFrame]
                                       ) -> TimeSeries:
    time_series_containers={}
    for name, df in data_all.items():
        time_series_containers[name] = _create_parent_timeseries(name, df)
    return time_series_containers
    
def _create_parent_timeseries(instrument_name: str,
                              data: pd.DataFrame
                              ) -> TimeSeries:
    data_metrics = data[["bid", "ask"]].values
    bid, ask = data_metrics[:,0], data_metrics[:,1]
    kwargs = {"name" : instrument_name,
              "metric_type" : "price",
              "timestamps" : data.index.tolist(),        
              "bid" : bid,
              "ask" : ask,
              }
    return classes_timeseries.ParentTimeSeries(**kwargs)


def concat_timeseries(timeserie_container: Dict[str, List[np.ndarray, np.ndarray]]):
    df_frames=[]
    cols = []
    di= pd.DataFrame()
    for name, timeseries_data in timeserie_container.items():
        df_i = pd.DataFrame(timeseries_data[1], index = timeseries_data[0], columns=[name])
        df_frames.append(df_i)
        if len(di) == 0:
            di = df_i
        else:
            di = pd.concat([di, df_i], axis=1, ignore_index=False)  
        cols.append(name)
    df = pd.concat([df_i for df_i in df_frames], axis=1, ignore_index=False, )
    df = df.sort_index()
    df = df.ffill(axis=0)
    df = df.dropna(axis=0)
    
    timestamps = df.index
    res_dict={}
    for col in df:
        res_dict[col] = df[col].values
    return timestamps, res_dict

def create_timeseries_indexes(timeseries_container: Dict[str, List[np.ndarray, np.ndarray]]):
    idx_container={}
    ts_combined = np.array([])
    
    for name, timeseries_data in timeseries_container.items():
        ts = timeseries_data[0]
        ts_combined = np.append(ts_combined, ts)
        
    for name, timeseries_data in timeseries_container.items():
        idx_container[name] = np.searchsorted(ts_combined, timeseries_data[0])

    
        
    
    
    
    
    