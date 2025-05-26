from __future__ import annotations
from typing import List, Dict, Union, Tuple, Callable, TYPE_CHECKING, ClassVar, Any
if TYPE_CHECKING:
    from instruments.classes import PriceInstrument, SyntheticInstrument, PriceInstrument
    

from dataclasses import dataclass, field

import numpy as np
import heapq
import ast, math
from custom_numpy import BufferArray

class DynamicMedian:
    def __init__(self, values: Union[List[float], None]=None):
        self.low = []  
        self.high = [] 
        self.values = [] 
        if not values is None:
            values_iter = iter(values)
            first = next(values_iter)
            heapq.heappush(self.low, -first)
            self.values.append(first)
            for v in values_iter:
                self.insert(v)

    def insert(self, value: float):
        self.values.append(value)
        if not self.low or value <= -self.low[0]:
            heapq.heappush(self.low, -value)
        else:
            heapq.heappush(self.high, value)

        if len(self.low) > len(self.high) + 1:
            heapq.heappush(self.high, -heapq.heappop(self.low))
        elif len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def median(self) -> float:
        if len(self.low) > len(self.high):
            return -self.low[0]
        return (-self.low[0] + self.high[0]) / 2

    def get_values(self) -> List[float]:
        return self.values


def spread(bid, ask):
    return ask - bid

def decimal_spread(bid, ask):
    return 2 * (ask - bid) / (bid + ask)

def pct_spread(bid, ask):
    return 100 * decimal_spread(bid, ask)

def mid(bid, ask):
    return 0.5 * (bid+ask)

def pct_returns(val_1: Union[np.ndarray, float],
                val_2: Union[np.ndarray, float]
               ) -> Union[np.ndarray, float]:
    return 100 * (val_2 / val_1 - 1)

def pct_returns_reverse(val_1: Union[np.ndarray, float],
                        val_2: Union[np.ndarray, float]
                        ) -> Union[np.ndarray, float]:
    return val_1 * (1 + val_2 / 100)

def returns(val_1: Union[np.ndarray, float],
            val_2: Union[np.ndarray, float]
            ) -> Union[np.ndarray, float]:
    return val_2 / val_1 - 1

def returns_reverse(val_1: Union[np.ndarray, float],
                    val_2: Union[np.ndarray, float]
                    ) -> Union[np.ndarray, float]:
    return val_1 * (1 + val_2)

def log_returns(val_1: Union[np.ndarray, float],
                val_2: Union[np.ndarray, float]
                ) -> Union[np.ndarray, float]:
    return np.log(val_2 / val_1)

def log_returns_reverse(val_1: Union[np.ndarray, float],
                        val_2: Union[np.ndarray, float]
                        ) -> Union[np.ndarray, float]:
    return val_1 * (np.exp(val_2))

def null_m(_, val_2):
    return val_2

def null_m_reverse(_, val_2):
    return val_2

def null(val):
    return val

def null_reverse(val):
    return val


@dataclass(slots=True, frozen=True)
class _BaseConverter:
    _base: Callable|None = field(default_factory=lambda: None)
    _decimal: Callable|None = field(default_factory=lambda: None)
    _pct: Callable|None = field(default_factory=lambda: None)
    _display_base: Callable|None = field(default_factory=lambda: None)
    _log: Callable|None = field(default_factory=lambda: None)
    
    def base(self, *args):
        return self._base(*args)
    
    def decimal(self, *args):
        return self._decimal(*args)

    def pct(self, *args):
        return self._pct(*args)
    
    def display_base(self, *args):
        return self._display_base(*args)
    
    def log(self, *args):
        return self._log(*args)

    
    

@dataclass(slots=True)
class MetricConverter:
    values: np.ndarray|BufferArray|None = field(default_factory=lambda: None)
    metric: str|None = field(default_factory=lambda: None)
    scale: str = field(default_factory=lambda: "base")
    static_param: float | None = field(default_factory=lambda: None)
    _static_off: bool  = field(default_factory=lambda: True)
    _parent_multi_value: bool  = field(default_factory=lambda: False)
    function: Callable = field(default_factory=lambda: None)
    get_price_function: Callable = field(default_factory=lambda: None)
    null_with_multi_arg: bool  = field(default_factory=lambda: False)
    converter: _BaseConverter = field(default=None)
    display_function: Callable = field(default_factory=lambda: None)
    
    def __post_init__(self):
        if self.metric is None:
            self.set_null()
        else:
            if self.metric == "price":
                if isinstance(self.values[0], (list, np.ndarray, BufferArray)):
                    self.static_param = mid(self.values[0][0], self.values[1][0])
                elif isinstance(self.values[0], float):
                    self.static_param=self.values[0]
                    
                self._static_off=False
                self.converter = _BaseConverter(mid, returns, pct_returns, null_m, log_returns) 
            elif self.metric == "spread":
                self.converter = _BaseConverter(spread, decimal_spread, pct_spread, spread)
            if self.scale == "base":
                self.display_function = getattr(self.converter, "display_base")
            else:
                self.display_function = getattr(self.converter, self.scale)
            
            
    def base(self, v1, v2):
        return self.converter.base(v1, v2)
    
    def convert_to_display(self, v1, v2):
        return self.display_function(v1, v2)
    
    def set_null(self):
        if self.null_with_multi_arg:
            self.converter = _BaseConverter(null_m, null_m, null_m, null_m, null_m) 
        else:
            self.converter = _BaseConverter(null, null, null, null, null) 

    def change_scale(self, scale):
        self.scale=scale
        if scale == "base":
            method = "display_base"
        else:
            method = scale          
        self.display_function = getattr(self.converter, method)

    
    def change_static_param(self, value):
        self.static_param = value

    @classmethod
    def find_function(cls,
                      metric_child: str,
                      metric_parent: str
                      ) -> Tuple[Callable, Callable]:
        if metric_parent == metric_child:
            return null, null_reverse
        
        match metric_child:
            case "pct_returns":
                return pct_returns, pct_returns_reverse

            case "returns":
                return returns, returns_reverse
            
            case "log_returns":
                return log_returns, log_returns_reverse

            case "mid":
                return mid, mid
            
            case "spread":
                return spread, spread
            
            case "decimal_spread":
                return decimal_spread, decimal_spread
            
            case "pct_spread":
                return pct_spread, pct_spread
            
            
    

_OPERATOR = {"sum" : "+",
             "product" : "*",
             }

_METRICS = {"price": "p1",
            "pct_returns": "100*(p2/p1-1)",
            "log_returns": "log(p2/p1)",
            "returns": "p2/p1-1",
            }

_FUNC_ARRAY = {"log": np.log,
               "exp": np.exp,
               "sqrt": np.sqrt}

_FUNC_SCALAR = {"log": math.log,
                "exp": math.exp,
                "sqrt": math.sqrt}

def _compiler_array(expr, extra=None):
    env = {**_FUNC_ARRAY, **(extra or {})}
    code = compile(ast.parse(expr, mode="eval"), "<expr>", "eval")
    return lambda d: eval(code, {"__builtins__": None, **env}, d)

def _compiler_scalar(expr, extra=None):
    env = {**_FUNC_SCALAR, **(extra or {})}
    code = compile(ast.parse(expr, mode="eval"), "<expr>", "eval")
    return lambda d: eval(code, {"__builtins__": None, **env}, d)



@dataclass(slots=True)
class MetricEngine:
    data: Union[Dict[str, float], List[str]] = field(default_factory=lambda: None)
    op_expr: str | None = field(default_factory=lambda: None)
    mode: str | None = field(default_factory=lambda: None)
    compiler_scalar: Callable = field(default_factory=lambda: None)
    compiler_array: Callable = field(default_factory=lambda: None)
    static_param: None = field(default_factory=lambda: None)

    def __post_init__(self):
        if self.op_expr is None:
            if self.mode in _OPERATOR:
                self.op_expr = self.create_expression(self.data, _OPERATOR[self.mode])
                
        self.compiler_scalar = _compiler_scalar(self.op_expr)
        self.compiler_array = _compiler_array(self.op_expr)
        
    def __call__(self, update_dict: Dict[str, float]) -> float|BufferArray|np.ndarray:
        self.data.update(update_dict)
        return self.compiler_scalar(self.data)
    
    def display_function(self, *args):
        return self.compiler_scalar(self.data)
    
    def convert_to_display(self, _, values):
        return values
    
    def change_static_param(self, *args):
        pass
    
    def change_scale(self, *args):
        pass
        
    def update_data_dict(self,
                         value: float,
                         name: str
                         ) -> None:
        self.data[name]=value
    
    def evaluate_array(self, values_dict):
        return self.compiler_array(values_dict)
    
    @classmethod
    def from_child_instrument_list(cls,
                                   metric: str,
                                   child_list: List[PriceInstrument | SyntheticInstrument | PriceInstrument]
                                   ) -> MetricEngine:
        
        if metric in _METRICS:
            metric_exp = _METRICS[metric]
        
        value_dict = {}
        for child in child_list:
            value_dict[child.identifier] = child
            
        return value_dict
    
    
    @classmethod
    def create_expression(cls,
                          data: Dict[str, float] | List[str],
                          metric: str):
        names=list(data.keys())
        return metric.join(names)
            

    
    def change_static_param(self, value):
        pass


    
    
    
       #     for callback in self.change_static_param_callbacks:
      #          callback(self)

  #  def add_change_static_param_callback(self, callback):
   #     self.change_static_param_callbacks.append(callback)
   
   
   

@dataclass(slots=True)
class MetricConverter22222222222:
    values: np.ndarray|BufferArray|None = field(default_factory=lambda: None)
    metric_child: str|None = field(default_factory=lambda: None)
    metric_parent: Union[str, List[str, str]] | None = field(default_factory=lambda: None)
    static_param: float | None = field(default_factory=lambda: None)
    _static_off: bool  = field(default_factory=lambda: True)
    _parent_multi_value: bool  = field(default_factory=lambda: False)
    function: Callable = field(default_factory=lambda: None)
    get_price_function: Callable = field(default_factory=lambda: None)
    null_with_multi_arg: bool  = field(default_factory=lambda: False)
    
    def __post_init__(self):
        if self.metric_child is None:
            self.set_null()
        else:
            if self.metric_child in ["pct_returns", "returns", "log_returns"]:
                self.static_param = self.values[0]     
                self._static_off=False
            if isinstance(self.metric_parent, list):
                self._parent_multi_value=True         
            if self.function is None or self.get_price_function is None:
                self.function, self.get_price_function = self.find_function(self.metric_child, self.metric_parent)

    def __call__(self, args) -> float|BufferArray|np.ndarray:
        if self._static_off:
            if self._parent_multi_value:
                return self.function(*args)
            return self.function(args)
        return self.function(self.static_param, args) 
        
    def change_function_static_params(self, value):
        self.static_param=value
    
    def get_prices(self, values):
        return self.get_price_function(self.static_param, values)
    
    def set_function(self, function: str, reverse_function: str):
        self.function, self.get_price_function = function, reverse_function

    def set_null(self):
        if self.null_with_multi_arg:
            self.function, self.get_price_function = null_m, null_m_reverse
        else:
            self.function, self.get_price_function = null, null_reverse
            
    @classmethod
    def find_function(cls,
                      metric_child: str,
                      metric_parent: str
                      ) -> Tuple[Callable, Callable]:
        if metric_parent == metric_child:
            return null, null_reverse
        
        match metric_child:
            case "pct_returns":
                return pct_returns, pct_returns_reverse

            case "returns":
                return returns, returns_reverse
            
            case "log_returns":
                return log_returns, log_returns_reverse

            case "mid":
                return mid, mid
    
    def change_metric_ty222pe(self, metric_type):
        self.metric_child=metric_type
        self.function, self.get_price_function = self.find_function(self.metric_child, self.metric_parent)
    
    def change_static_param(self, value):
        print(f"change_static_param")
        self.static_param = value
