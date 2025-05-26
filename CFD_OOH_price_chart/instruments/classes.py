from __future__ import annotations
from typing import Callable, Sequence, List, Dict, NoReturn, Union, Tuple, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from instruments.classes import SyntheticInstrument
    from instruments.classes import InstrumentContainer
    from mathematics.numerics import MetricEngine, MetricEngine
    from timeseries.classes import TimeSeries
    from custom_numpy import BufferArray

from dataclasses import dataclass, field, InitVar, fields, replace, asdict
import datetime
from itertools import permutations
from abc import ABC, abstractmethod
from datetime import datetime
from weakref import WeakMethod
import traceback

@dataclass(slots=True, kw_only=True, frozen=True)
class InstrumentSpecs:
    name: str
    asset_class: str | None
    exchange: Union[str, None]
    auction_period: Union[Tuple[datetime.time, datetime.time], None]
    close_time: Union[datetime.time, None]
    open_time: Union[datetime.time, None]
    timezone: Union[str, None]
    breaks: Union[List[Tuple[datetime.time, datetime.time]], None]
    weekday_open_schedule: Union[int, None]
    weekday_closed_schedule: Union[int, None]
    holiday_schedule: Union[Dict[datetime.date, Union[datetime.time, str]], None]
    same_day_OOH: bool = field(init=False)  
    
    def __post_init__(self):
        same_day = False
        if self.close_time is not None and self.open_time is not None:
            same_day = self.close_time < self.open_time
        object.__setattr__(self, 'same_day_OOH', same_day)

    @classmethod
    def from_parent(cls,
                    other: InstrumentSpecs,
                    kwargs: Dict[str, Any] = None,
                    ) -> InstrumentSpecs:
        
        return replace(other, **kwargs)
    
    
@dataclass(kw_only=True)
class InstrumentInfo:
    market_open: bool
    check_market_status: Callable[[float], Callable]
    current_period: Union[Tuple[float], None] = field(default_factory=lambda: None)

@dataclass(kw_only=True, slots=True)
class _AbstractInstrument(ABC):
    specs: InstrumentSpecs
    info: InstrumentInfo
    metric_type: str

    @property
    def name(self):
        return self.specs.name
    @property
    def name(self):
        return self.specs.name
    
    @abstractmethod
    def get_value_kwargs(self):
        ...



@dataclass(kw_only=True)
class BaseInstrument(_AbstractInstrument):
    _metric_values: List[float] | None = field(default_factory=lambda: [])
    
    timestamp: float
    display_name: str = field(default_factory=lambda: None)
    update_callbacks: List[Callable] = field(default_factory= lambda: [])    

    @abstractmethod
    def update(self, **kwargs):
        ...

    def add_update_callback(self, callback):
        self.update_callbacks.append(callback)
        #self.update_callbacks.append(WeakMethod(callback))

    def remove_update_callback(self, callback):
        if len(self.update_callbacks) > 0:
            self.update_callbacks.remove(callback)

    def update_cleanup(self) -> None:
        for callback in self.update_callbacks:
            callback(self)
    
    @property
    def check_market_status(self) -> bool:
        return self.info.check_market_status(self.timestamp)

    def create_child(self,
                     class_name_child: str,
                     kwargs_child: Dict[str, Any],
                     ) -> SyntheticInstrument:
        cls = globals()[class_name_child]
        kwargs_child["timestamp"] = self.timestamp
        
        if not "specs" in kwargs_child:
            kwargs_child["specs"] = self.specs
        if not "info" in kwargs_child:
            kwargs_child["info"] = self.info
        
        child = cls(**kwargs_child)  
        self.add_update_callback(child.update)
        return child

    @abstractmethod
    def get_metric_values(self) -> Tuple[float, float] | float:
        ...

    @abstractmethod
    def get_value_kwargs(self):
        ...

    @classmethod
    def from_parent(cls,
                    parent_instrument: PriceInstrument | SyntheticInstrument,
                    kwargs_to_update: None=None
                    ):
        
        parent_kwargs = asdict(parent_instrument)
        if not kwargs_to_update is None:
            parent_kwargs.update(kwargs_to_update)

        return cls(**parent_kwargs)

    

@dataclass(kw_only=True)
class PriceInstrument(BaseInstrument):
    
    _bid: float = field(default=None, init=False, repr=False)
    _ask: float = field(default=None, init=False, repr=False)
    _mid: float = field(default=None, init=False, repr=False)
    metric_type: str = "price"

    bid: float | None = field(default_factory=lambda: None)
    ask: float | None = field(default_factory=lambda: None)         
            
    def update(self, timestamp=None, bid=None, ask=None):
        if not timestamp is None:
            self.timestamp = timestamp            
        if not bid is None:
            self.bid = bid
        if not ask is None:
            self.ask = ask
        self.update_cleanup()
        
    def update_cleanup(self) -> None:
        for callback in self.update_callbacks:
            callback(self)
    
    def get_metric_values(self) -> Tuple[float, float]:
        return self._metric_values
    
    def get_value_kwargs(self,
                         metric: str=None
                         ) -> Dict[str, float] | float:
        if not metric is None:
            return getattr(self, metric)
        else:
            return {"bid" : self.bid, "ask" : self.ask}
    
    @property
    def value(self) -> float:
        return self._bid, self._ask
    
    @property
    def bid(self) -> float:
        return self._bid
    
    @bid.setter
    def bid(self, value: float) -> None:
        self._bid = value

    @property
    def ask(self) -> float:
        return self._ask
    
    @ask.setter
    def ask(self, value: float) -> None:
        self._ask = value
    

@dataclass(slots=True, kw_only=True)
class SyntheticInstrument(BaseInstrument):
    basket: Dict[str, float] = field(default_factory=dict)
    value: float = field(default_factory=lambda: None)
    value_attr_parent: Dict[str, str] = field(default=dict)
    engine: MetricEngine = field(default_factory=lambda: None)
    metric_calculator: MetricEngine = field(default_factory=lambda: None)   
    
    def __post_init__(self):
        super(SyntheticInstrument, self).__post_init__()
        if all(self.basket.values()) and self.value is None:
            self.update_no_callback()
            
    def update(self, parent_object: PriceInstrument | SyntheticInstrument | TimeSeries):
        self.timestamp = parent_object.timestamp
        self.basket[parent_object.name] = self.metric_calculator(getattr(parent_object, self.value_attr_parent[parent_object.name])())
        self.value = self.engine(self.basket)
        self.update_cleanup()
    
    def update_basket_value(self,
                            name: str,
                            value:float
                            ) -> None:
        self.basket[name]=value
    
    def update_no_callback(self) -> None:
        self.value = self.engine(self.basket)
    
    def evaluate_series(self, array: Dict[str, BufferArray]):
        return self.engine.evaluate_array(array)
        
    def get_metric_values(self):
        return self.value

    def get_value_kwargs(self, name):
        return {"value" : self.value}








































