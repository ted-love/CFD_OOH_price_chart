from instruments.classes import PriceInstrument
from typing import List, Dict, Callable, Tuple
from dataclasses import dataclass, field
from instruments.classes import PriceInstrument
from typing import List, Dict, Callable, Union
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from typing import Dict, Callable
from pprint import pformat
from mathematics.numerics import DynamicMedian
import numpy as np



@dataclass(slots=True, kw_only=True)
class WeightMetrics:
    name_follower: str
    leader_names: List[str]
    configs: Dict[str, Dict[str, Union[float, int]]]
    dynamic_median_container: Dict[str, DynamicMedian] 
    subset_median_container: Dict[str, DynamicMedian]  
    subset_median_container_prev: Dict[str, DynamicMedian] 
    weight_list_container: Dict[str, List[float]]
    weight_list_container_n: Dict[str, List[float]]
    weight_changes_container: Dict[str, Tuple[float, float]]
    
    theo_weights: Dict[str, Dict[str, Dict[str, float]]]
    metrics: Dict[str, float]
    notify_median_change_callbacks: Dict[str, List[Callable]]
    adjustment_listeners: Dict[str, List[Callable]]
    n_max: int
    update_callbacks: Dict[str, List[Callable]] = field(default_factory=dict)
    same_response: Dict[str, List[bool]] = field(default_factory=lambda:[])
    resp: List[filter] = field(default_factory=lambda:[])
    _weight_counter_container: Dict[str, int] = field(default_factory=dict)
    def __post_init__(self):
        self._weight_counter_container = {name_leader : 2 for name_leader in self.leader_names}
        self.notify_median_change_callbacks = {name_leader : [] for name_leader in self.leader_names}
        self.same_response = {name : [] for name in self.leader_names}
        self.resp = {name : [] for name in self.leader_names}
    
    def add_weight_changed_callback(self, leader_name, callback):
        self.notify_median_change_callbacks[leader_name].append(callback)
    
    def add_update_callback(self, leader_name, callback):
        self.update_callbacks.update({leader_name: callback})   
    
    def update(self, name_leader, timestamp_leader, value_leader, value_follower):
        same_response=False
        weight = 100 * round(value_follower / value_leader, self.configs["rounding"]["weight"])
        resp_w=weight

        if abs(weight - self.theo_weights[name_leader]["main"]) < self.configs["tolerance"]["dw"]:
            same_response=True
        else:
            for ratio in self.theo_weights[name_leader]["ratio_map"].values():
                
                if abs(weight * ratio - self.theo_weights[name_leader]["main"]) < self.configs["tolerance"]["dw"]:
                    same_response=True
                    resp_w = weight * ratio
                    break
        self.same_response[name_leader].append(same_response)
        self.resp[name_leader].append(weight)
        self.weight_list_container_n[name_leader].append(resp_w)
        if len(self.same_response[name_leader]) == self.n_max:
            n_true = sum(self.same_response[name_leader])
            if n_true < self.n_max / 2:
                for callback in self.notify_median_change_callbacks[name_leader]:
                    callback(name_leader, timestamp_leader)

            self.same_response[name_leader]=[]
            self.resp[name_leader]=[]
            
        self.dynamic_median_container[name_leader].insert(weight)
        self.subset_median_container[name_leader].insert(weight)
        self.weight_list_container[name_leader].append(resp_w)
        self.metrics[name_leader] = self.dynamic_median_container[name_leader].median()
    
        self._weight_counter_container[name_leader]+=1 
        if self._weight_counter_container[name_leader] == self.n_max:
            self._check_weight_intervals(name_leader)
            self._weight_counter_container[name_leader]=0
            self.subset_median_container_prev[name_leader] = self.subset_median_container[name_leader]
            self.subset_median_container[name_leader]=DynamicMedian(self.subset_median_container[name_leader].get_values()[-2:])

        for name, callback in self.update_callbacks.items():
            callback(np.median(self.weight_list_container_n[name][-self.n_max:]))    
            
    def _check_weight_intervals(self, name_leader):
        
        median_prev = self.subset_median_container_prev[name_leader].median()
        median = self.subset_median_container[name_leader].median()
    
        if abs(median - median_prev) > self.configs["tolerance"]["dw"]:
            if len(self.notify_median_change_callbacks) > 0:
                return 
                for callback in self.notify_median_change_callbacks[name_leader]:
                    callback(name_leader)
            
    def _check_time_diff(self, follower_ts, leaderts):
        if follower_ts - leaderts < self.configs["tolerance"]["dt"]:
            return True
        else:
            return False

    
    def process_response(self, follower_data: Dict[str, float], leaderdata: Dict[str, float]):
        if self._check_time_diff(follower_data["timestamp"], leaderdata["timestamp"]):
            self.update(leaderdata["name_leader"],
                        leaderdata["timestamp"],
                        leaderdata["delta"],
                        follower_data["delta"])
                
          


@dataclass(slots=True, kw_only=True)
class Node(ABC):
    """Base class for Leader and Follower nodes with common attributes/methods."""
    name: str
    init_price: float
    last_timestamp: float
    last_price: float
    last_return: float
    last_delta: float

    @abstractmethod
    def update_from_instrument(self, instrument: PriceInstrument):  # Use BaseInstrument type
        pass

    def __repr__(self):
        return pformat(asdict(self), indent=2, width=80, depth=3)
    
    def __str__(self):
        return self.__repr__()

@dataclass(slots=True, kw_only=True)
class Leader(Node):
    last_response_container: Dict[float, float] = field(default_factory=lambda: {})
        

    def update_from_instrument(self, instrument: PriceInstrument):
        self.last_timestamp = instrument.timestamp
        self.last_price = 0.5 *(instrument.bid+instrument.ask)
        returns = 100 * (self.last_price / self.init_price - 1)
        self.last_delta = returns - self.last_return
        self.last_response_container[self.last_timestamp]=self.last_delta
        self.last_return = returns

    def last_values(self, timestamp_follower):
        last_timestamp, last_delta = self.last_timestamp, self.last_delta
        for ts, delta in self.last_response_container.items():  
            if ts < timestamp_follower:
                last_timestamp = ts
                last_delta=delta
            else:
                break
        return last_timestamp, last_delta

@dataclass(slots=True, kw_only=True)
class Follower(Node):
    response_data_delta: Dict[str, Dict[float, Dict[str, float]]]
    weight_metrics: WeightMetrics 
    leader_callbacks: Dict[str, Callable]
    leaders_last_ts: Dict[str, float]
    cached_data_follower: Dict[str, float] = field(default_factory=lambda: {"timestamp": None, "delta": None})
    cached_data_leader: Dict[str, float] = field(default_factory=lambda: {"name": None, "timestamp": None, "delta": None})

    def update_from_instrument(self, instrument: PriceInstrument):
        returns = 100 * (0.5 *(instrument.bid+instrument.ask) / self.init_price - 1)
        delta_follower = returns - self.last_return
        self.cached_data_follower["timestamp"] = instrument.timestamp
        self.cached_data_follower["delta"] = delta_follower
        self.last_return = returns
        
        for name_leader, callback in self.leader_callbacks.items():
            timestamp_leader, delta_leader = callback(self.cached_data_follower["timestamp"])
            self.cached_data_leader["name_leader"] = name_leader
            self.cached_data_leader["timestamp"] = timestamp_leader
            self.cached_data_leader["delta"] = delta_leader
            
            if delta_leader != 0 and delta_follower != 0:
                self.weight_metrics.process_response(self.cached_data_follower, self.cached_data_leader)
                if timestamp_leader > self.leaders_last_ts[name_leader]:
                    self.response_data_delta[name_leader][instrument.timestamp] = {self.name: delta_follower,
                                                                                name_leader: delta_leader}
                    self.leaders_last_ts[name_leader] = timestamp_leader
                #    self.weight_metrics.update(name_leader, delta_leader, delta_follower)
            
        self.last_delta = delta_follower
        self.last_timestamp = instrument.timestamp
