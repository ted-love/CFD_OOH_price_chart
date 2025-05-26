from __future__ import annotations
from typing import Callable, Sequence, List, Dict, NoReturn, Union, Tuple, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from timeseries.classes import ParentTimeSeries, TimeSeries
    from instruments.classes import InstrumentContainer, PriceInstrument, SyntheticInstrument
    from subplot_structure.classes import SubPlotStructure

from timeseries.classes import TimeSeries
from instruments.classes import PriceInstrument
import pandas as pd
import numpy as np
from time_helpers.classes import PatchedDateTime
from .classes import Follower, Leader
import pytz
from time_helpers import builders as builders_time_helpers
from mathematics import numerics as math_numerics

from time_helpers import utils as utils_time_helpers
from instruments.classes import PriceInstrument
from . import classes as classes_ig_measuring
from . import config as config_ig_measuring

def create_weight_metrics(subplot_structure_container: Dict[str, SubPlotStructure],
                          configs: Dict[str, str[Dict[str, List[str]]]]
                        ) -> None:   
                        
    
    for subplot_title, config in configs.items():
        if subplot_title in subplot_structure_container:
            leader_names = config["instrument_roles_configs"]["leader_instruments"]
            follower_names = config["instrument_roles_configs"]["follower_instruments"]
            
            subplot_structure = subplot_structure_container[subplot_title]
            instrument_container = subplot_structure.instrument_parent_container
            timeseries_container = subplot_structure.timeseries_container
                
            follower_container={}
            leader_container={}
            
            if all([name in subplot_structure.instrument_names for name in leader_names]):
                
            
                for name_follower in follower_names:
                    instrument_follower = instrument_container[name_follower]
                    timeseries_follower = timeseries_container[name_follower]
                    

                    
                    
                    timestamps_follower, prices_follower = timeseries_follower.get_data()
                    init_price_follower = prices_follower[0]
                    price_series_follower = pd.Series(prices_follower, index=timestamps_follower)
                    pct_returns_follower = 100 * (price_series_follower / init_price_follower - 1)
                    delta_follower_map = pct_returns_follower.diff().to_dict()
                    delta_follower = pct_returns_follower.diff().values
                    price_follower = price_series_follower.to_dict()
                    
                    timeseries_leaders={}
                    response_data_delta = {name : {} for name in leader_names}
                    leader_callbacks={}
                    last_timestamp_leaders={}
                    
                    dynamic_medians={}
                    subset_dynamic_medians={}
                    subset_dynamic_medians_prev={}
                    metrics={}
                    weight_list_container={}
                    weight_list_container_n={}
                    weight_changes_container={name : {} for name in leader_names} 
                    theo_weights={}
                    for name_leader in leader_names:
                        timeseries_leader = timeseries_container[name_leader]

                        
                        timestamps_leader, prices_leader = timeseries_leader.get_data()
                        init_price_leader=prices_leader[0]
                        price_series_leader = pd.Series(prices_leader, index=timestamps_leader)
                        pct_returns_leader = 100 * (price_series_leader / init_price_leader - 1)
                        
                        delta_leader = pct_returns_leader.diff()
                        last_delta_leader = delta_leader.iloc[-1]
                        last_timestamp_leader=timestamps_leader[-1]
                        delta_leader = delta_leader.to_dict()
                        price_leader = price_series_leader.to_dict()

                        weights={}
                        
                        
                        ts_weights=[]
                        k = 20
                        weight_ts_diff_map = {}
                        counts={}
                        barrier=0
                        for idx, ts_leader in enumerate(timestamps_leader):
                            if np.isnan(delta_leader[ts_leader]):
                                continue
                            ts_follower = timestamps_follower[(ts_leader <= timestamps_follower) & (ts_leader + config["tolerance"]["dt"] >= timestamps_follower) & (ts_leader > barrier)]
                            barrier = ts_leader + config["tolerance"]["dt"]
                            if len(ts_follower) > 0 and delta_leader[ts_leader] != 0:
                                d_leader = delta_leader[ts_leader]
                                d_follower = delta_follower_map[ts_follower[0]]
                                inner_dict = {name_follower : d_follower,
                                            name_leader : d_leader}
                                weight = 100 * (d_follower / d_leader)
                                weights[ts_leader] =weight
                            if len(ts_follower) == 1 and delta_leader[ts_leader] != 0:
                                d_leader = delta_leader[ts_leader]
                                d_follower = delta_follower_map[ts_follower[0]]
                                inner_dict = {name_follower : d_follower,
                                            name_leader : d_leader}
                                weight = 100 * (d_follower / d_leader)
                                weights[ts_leader] =weight

                                diff = ts_follower[0] - ts_leader
                                if not round(weight,1) in weight_ts_diff_map:
                                    
                                    weight_ts_diff_map[round(weight, 1)]=[np.floor(diff / 0.005) * 0.005]
                                    weight_ts_diff_map[round(weight, 1)] = []
                                else:
                                    weight_ts_diff_map[round(weight,1)].append(np.floor(diff / 0.005) * 0.005)
                            
                        from pprint import pprint
                        
                        for key, values in weight_ts_diff_map.items(): 
                            counts[key] = len(values)
                            weight_ts_diff_map[key] = np.median(values)
                        
                        sorted_dict = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))
                        filtered_weights = [weight for idx, weight in enumerate(sorted_dict.keys()) if idx < 6]
                        
                        theo_weights[name_leader] = {"main" : filtered_weights[0],
                                                    "ratio_map" : {weight : filtered_weights[0] / weight for weight in filtered_weights[1:] if weight > 0}}
                        response_data_delta[name_leader][ts_leader] = inner_dict
                        weights[ts_leader] = weight
                        ts_weights.append(ts_leader)
                                                        
                        leader_object = classes_ig_measuring.Leader(name=name_leader,
                                                                    init_price=init_price_leader,
                                                                    last_timestamp=last_timestamp_leader,
                                                                    last_price=prices_leader[-1],
                                                                    last_return=pct_returns_leader.iloc[-1],
                                                                    last_delta=last_delta_leader                                                        
                                                                    )

                        instrument_parent_leader = instrument_container[name_leader]

                        instrument_parent_leader.add_update_callback(leader_object.update_from_instrument)
                        
                        if name_leader in leader_container:
                            leader_container[name_leader][name_follower] = leader_object
                        else:
                            leader_container[name_leader] = {name_follower : leader_object}
                        
                        
                        leader_callbacks[name_leader] = leader_object.last_values
                        last_timestamp_leaders[name_leader] = last_timestamp_leader

                        timeseries_leaders[name_leader] = timeseries_leader
                        
                        dynamic_medians[name_leader] = math_numerics.DynamicMedian(list(weights.values()))

                        subset_dynamic_medians[name_leader] = math_numerics.DynamicMedian(dynamic_medians[name_leader].get_values()[-2:])
                        subset_dynamic_medians_prev[name_leader] = math_numerics.DynamicMedian(dynamic_medians[name_leader].get_values()[-2-k:-2])
                        weight_list_container[name_leader] = dynamic_medians[name_leader].get_values()

                        metrics[name_leader] = dynamic_medians[name_leader].median()
                        ki=k
                        ki_prev=0
                        weight_changes=[]
                        resp_collection=[]
                        while ki < len(dynamic_medians[name_leader].get_values()):
                            w = weight_list_container[name_leader][ki_prev:ki]
                            bools=[]
                            resp_w=[]
                            for wi in w:
                                if abs(wi - theo_weights[name_leader]["main"]) < config["tolerance"]["dw"]:
                                    resp_w.append(wi)
                                    bools.append(True)
                                    continue
                                else:
                                    continue_flag=False
                                    for ratio in theo_weights[name_leader]["ratio_map"].values():
                                        
                                        if abs(wi * ratio - theo_weights[name_leader]["main"]) < config["tolerance"]["dw"]:
                                            bools.append(True)
                                            continue_flag=True
                                            resp_w.append(abs(wi * ratio))
                                            break
                                if continue_flag:
                                    continue
                                resp_w.append(wi)
                                bools.append(False)
                            if sum(bools) < k/2:
                                weight_changes.append(ki_prev)
                            resp_collection = resp_collection + resp_w
                            ki_prev=ki
                            ki+=k
                        weight_changes_container[name_leader]=weight_changes
                        weight_list_container_n[name_leader]=resp_collection
                            
                            
                    
                    weight_metrics = classes_ig_measuring.WeightMetrics(name_follower=name_follower,
                                                                        leader_names=leader_names,
                                                                        configs=config,
                                                                        dynamic_median_container=dynamic_medians,
                                                                        subset_median_container=subset_dynamic_medians,
                                                                        subset_median_container_prev=subset_dynamic_medians_prev,
                                                                        weight_changes_container=weight_changes_container,
                                                                        
                                                                        weight_list_container=weight_list_container,
                                                                        weight_list_container_n=weight_list_container_n,
                                                                        theo_weights=theo_weights,
                                                                        metrics=metrics,
                                                                        notify_median_change_callbacks={},
                                                                        adjustment_listeners={},                                                            
                                                                        n_max=20)

                    follower_object = classes_ig_measuring.Follower(name=name_follower,
                                                                    init_price=init_price_follower,
                                                                    last_timestamp=timestamps_follower[-1],
                                                                    last_price=prices_follower[-1],
                                                                    last_return=pct_returns_follower.iloc[-1],
                                                                    last_delta=delta_follower[-1],
                                                                    response_data_delta=response_data_delta,
                                                                    weight_metrics=weight_metrics,
                                                                    leader_callbacks=leader_callbacks,
                                                                    leaders_last_ts=last_timestamp_leaders)
                    instrument_parent_follower = instrument_container[name_follower]
                    instrument_parent_follower.add_update_callback(follower_object.update_from_instrument)
                    
                    follower_container[name_follower] = follower_object
                subplot_structure.ig_measuring_followers = follower_container


