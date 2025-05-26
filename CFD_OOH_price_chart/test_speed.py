#%%%


from dataclasses import dataclass, field

class myclass:
    x:bool = field(init=False, default_factory=lambda: False)
    def func(self):
        self.x=False
xx = myclass()
xx.x
#%%
import timeit

N = 1000

setup_code1 = f"""
import numpy as np
limits = np.random.normal(0, 1, size=(5,4)).tolist()
idx=0

"""

setup_code2 = f"""
import numpy as np
limits = np.random.normal(0, 1, size=(5,4)).tolist()
"""
func1="""
idx=0

for l in limits:
    if idx == 0:
        xmin, xmax, ymin, ymax = l
        idx += 1 
        continue
        
    if l[0] < xmin:
        xmin = l[0]
    elif l[1] > xmax:
        xmax = l[1]
    if l[2] < ymin:
        ymin = l[2]
    elif l[3] > ymax:
        ymax = l[3]
           
        
"""

func2="""
xmi, xma,ymi, yma=[],[],[],[]
for l in limits:
    xx,xxx,yy,yyy=l
    xmi.append(xx)
    xma.append(xxx)
    ymi.append(yy)
    yma.append(yyy)

xmin,xmax,yminm,ymax = min(xmi), max(xma), min(ymi), max(yma)

"""


time_small = timeit.timeit(func1, setup=setup_code1, number=1000000)
time_large = timeit.timeit(func2, setup=setup_code2, number=1000000)

print(f"Time with smaller array: {time_small:.6f} seconds")
print(f"Time with larger array: {time_large:.6f} seconds")


#%%

import timeit

setup_code = """
import numpy as np
arr = np.arange(10000)
idx_filter = [200, 5000]
"""

stmt1 = "arr[idx_filter[0]:idx_filter[1]]"
stmt2 = "arr[slice(*idx_filter)]"

time1 = timeit.timeit(stmt1, setup=setup_code, number=5_0000_000)
time2 = timeit.timeit(stmt2, setup=setup_code, number=5_0000_000)

print(f"arr[idx_filter[0]:idx_filter[1]]: {time1:.6f} seconds")
print(f"arr[slice(*idx_filter)]:       {time2:.6f} seconds")


#%%

import numpy as np
import math
import ast

import timeit


# Setup code as a string
setup_code1 = """

import numpy as np
import math
import ast


_METRICS = {"pct_returns" : "100*(p2/p1-1)",
            "log_returns" : "log(p2/p1)",
            "decimal_returns" : "p2/p1-1",
            }

_METRICS = {"price" : "p1"} | _METRICS


_FUNC_ARRAY = {"log": np.log, "exp": np.exp, "sqrt": np.sqrt}
_FUNC_SCALAR = {"log": math.log, "exp": math.exp, "sqrt": math.sqrt}

def _compiler_array(expr, extra=None):
    env = {**_FUNC_ARRAY, **(extra or {})}
    code = compile(ast.parse(expr, mode="eval"), "<expr>", "eval")
    return lambda d: eval(code, {"__builtins__": None, **env}, d)

def _compiler_scalar(expr, extra=None):
    env = {**_FUNC_SCALAR, **(extra or {})}
    code = compile(ast.parse(expr, mode="eval"), "<expr>", "eval")
    return lambda d: eval(code, {"__builtins__": None, **env}, d)


class _dummy_compiler:
    def __init__(self, expr):
        self.expr=expr
    
    def __call__(self, value_dict):
        return value_dict[self.expr]    

class MetricEngine:
    def __init__(self,
                 data,
                 op_expr: str=None,
                 metric: str=None
                ):
        self.value_dict=data
        if op_expr is None:
            self.op_expr= self.create_expression(data, metric=metric)
        else:
            self.op_expr=op_expr
        
        self.compiler_array = _compiler_array(self.op_expr)
        self.compiler_scalar = _compiler_scalar(self.op_expr)

    def evaluate_scalar(self, value_dict):
        return self.compiler_scalar(value_dict)
    
    def evaluate_array(self, value_dict):
        return self.compiler_array(value_dict)

    @classmethod
    def from_child_instrument_list(cls,
                                   metric: str,
                                   child_list):
        if metric in _METRICS:
            metric_exp = _METRICS[metric]
        
        value_dict = {}
        for child in child_list:
            value_dict[child.identifier] = child
            
        return value_dict
    
    @classmethod
    def create_returns_expression(cls, instrument_name, metric):
        op_expr=_METRICS[metric]
        p2 = instrument_name
        p1 = f"{instrument_name}_0"

        op_expr = op_expr.replace("p1", p1)
        op_expr = op_expr.replace("p2", p2)
        return op_expr
    
    
    @classmethod
    def create_expression(cls, data, metric):
        if metric in _METRICS:
            op_expr=_METRICS[metric]
            for name in data:
                if "_0" in name:
                    p1=name
                else:
                    p2=name


            op_expr = op_expr.replace("p1", p1)
            op_expr = op_expr.replace("p2", p2)
        return op_expr

data = {"p2" : 20,
        "p1" : 10}
op_expr = "100*(p2/p1-1)"
engine = MetricEngine(data, op_expr)




"""

setup_code2 = """


from dataclasses import dataclass, field
def pct_returns(val_1, val_2):
    return 100 * (val_2 / val_1 - 1)


@dataclass
class MetricCalculator:
    S_0: float | None = field(default_factory=lambda: None)
    function: float = field(default_factory=lambda: None)
    
    def __call__(self, values):
        return self.function(self.S_0, values) 

value = 10
mc = MetricCalculator(20, pct_returns)


"""



func1 = """

engine.evaluate_scalar(data)

"""
func2 = """

mc(value)

"""





# Time calling return_float()
time_float = timeit.timeit(func1, setup=setup_code1, number=10000000)

# Time calling return_int()
time_int = timeit.timeit(func2, setup=setup_code2, number=10000000)

print(f"Time for return_float(): {time_float:.6f} seconds")
print(f"Time for return_int(): {time_int:.6f} seconds")
#%%

arr1 = np.linspace(5,6, 5)
arr2 = 2*np.linspace(4,5,4)


arr1_0 = arr1[0]
arr2_0 = arr2[0]

c1 = arr1 / arr1_0 - 1
c2 = arr2 / arr2_0 - 1 

ts1 = np.array([3,4,9,20,55]) 

ts2 = np.array([3,4,6,21])

ts_s = np.unique(np.concatenate((ts1, ts2)))

c_s = np.zeros_like(ts_s, dtype=float)

idx1 = np.searchsorted(ts_s, ts1)
idx2 = np.searchsorted(ts_s, ts2)

np.add.at(c_s, idx1, c1)
np.add.at(c_s, idx2, c2)
c_s



filter_t =3.5

idx1_f = ts1 >= filter_t
idx2_f = ts2 >= filter_t

ts1_f = ts1[idx1_f]
ts2_f = ts2[idx2_f]


arr1_f = arr1[idx1_f]
arr2_f = arr2[idx2_f]

arr1_f_0 = arr1_f[0]
arr2_f_0 = arr2_f[0]


c1_f = arr1_f / arr1_f_0 - 1
c2_f = arr2_f / arr2_f_0 - 1 

idx_s = ts_s >= filter_t

ts_s_f = ts_s[ts_s >= filter_t]

c_s_f_correct = np.zeros_like(ts_s_f, dtype=float)

idx1_f_s = np.searchsorted(ts_s_f, ts1_f)
idx2_f_s = np.searchsorted(ts_s_f, ts2_f)

np.add.at(c_s_f_correct, idx1_f_s, c1_f)
np.add.at(c_s_f_correct, idx2_f_s, c2_f)


from typing import Union, Dict, List, Tuple, Callable



def pct_returns(val_1: Union[np.ndarray, float], val_2: Union[np.ndarray, float]
               ) -> Union[np.ndarray, float]:
    return 100 * (val_2 / val_1 - 1)

def pct_returns_reverse(val_1: Union[np.ndarray, float], val_2: Union[np.ndarray, float]
                        ) -> Union[np.ndarray, float]:
    return val_1 * (1 + val_2 / 100)

def returns(val_1: Union[np.ndarray, float], val_2: Union[np.ndarray, float]
            ) -> Union[np.ndarray, float]:
    return val_2 / val_1 - 1

def returns_reverse(val_1: Union[np.ndarray, float], val_2: Union[np.ndarray, float]
                    ) -> Union[np.ndarray, float]:
    return val_1 * (1 + val_2)

def log_returns(val_1: Union[np.ndarray, float], val_2: Union[np.ndarray, float]
                ) -> Union[np.ndarray, float]:
    return np.log(val_2 / val_1)

def log_returns_reverse(val_1: Union[np.ndarray, float], val_2: Union[np.ndarray, float]
                        ) -> Union[np.ndarray, float]:
    return val_1 * (np.exp(val_2))

def null(_, val_2):
    return val_2

def null_reverse(_, val_2):
    return val_2


_METRICS = {"price": "p1",
            "pct_returns": "100*(p2/p1-1)",
            "log_returns": "log(p2/p1)",
            "decimal_returns": "p2/p1-1",
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


@dataclass
class MetricEngine:
    name: str
    values: np.ndarray = field(default_factory=lambda: None)
    data: Union[Dict[str, float], List[str]] = field(default_factory=lambda: None)
    metric_child: str | None = field(default_factory=lambda: None)
    metric_parent: str | None = field(default_factory=lambda: None)
    static_param: Union[float, None] = field(default_factory=lambda: None)
    op_expr: str | None = field(default_factory=lambda: None)
    metric: str | None = field(default_factory=lambda: None)
    change_static_param_callbacks: List[Callable] = field(default_factory=list)

    def __post_init__(self):
        self.use_native = self.metric_child in ["pct_returns", "returns", "decimal_returns"]
        if self.use_native:
            if self.metric_child is None:
                self.set_null()
            else:
                if self.values is not None:
                    self.static_param = self.values[0]
                self.function, self.get_price_function = self.find_function(self.metric_child, self.metric_parent)
        else:
            if self.op_expr is None and self.metric is not None:
                self.op_expr = self.create_expression(self.data, self.metric)
            if self.op_expr is not None:
                self.compiler_array = _compiler_array(self.op_expr)
                self.compiler_scalar = _compiler_scalar(self.op_expr)

    def __call__(self,
                 values: float|np.ndarray):
        if self.use_native:
            return self.function(self.static_param, values)
        else:
            return self.compiler_scalar(values)

    def evaluate_array(self, value_dict):
        if not self.use_native:
            return self.compiler_array(value_dict)
        else:
            raise AttributeError("evaluate_array not available for native metrics")

    def get_prices(self, values):
        if self.use_native:
            return self.get_price_function(self.static_param, values)
        else:
            raise AttributeError("get_prices not available for compiled metrics")

    def set_null(self):
        self.function, self.get_price_function = null, null_reverse

    def find_function(self, metric_child, metric_parent):
        if metric_parent == metric_child:
            return null, null_reverse
        if metric_child == "pct_returns":
            return pct_returns, pct_returns_reverse
        elif metric_child == "returns":
            return returns, returns_reverse
        elif metric_child == "decimal_returns":
            return returns, returns_reverse
        else:
            return null, null_reverse

    @classmethod
    def create_expression(cls, data, metric):
        if metric in _METRICS:
            op_expr = _METRICS[metric]
            p1, p2 = None, None
            for name in data if isinstance(data, dict) else data:
                if "_0" in name:
                    p1 = name
                else:
                    p2 = name
            if p1 and p2:
                op_expr = op_expr.replace("p1", p1).replace("p2", p2)
            return op_expr
        return None

    @classmethod
    def from_child_instrument_list(cls, metric, child_list):
        value_dict = {}
        for child in child_list:
            value_dict[child.identifier] = child
        return cls(data=value_dict, metric=metric)

    def change_static_param(self, value):
        if self.use_native:
            self.static_param = value
            for callback in self.change_static_param_callbacks:
                callback(self)

    def add_change_static_param_callback(self, callback):
        self.change_static_param_callbacks.append(callback)
        
data = {"c1" : c1[-1],
        "c2" : c2[-1],
        }        
op_expr  = "c1+c2"

me = MetricEngine(data, op_expr=op_expr)

value_dict = {"c1" : c1,
              "c2" : c2}
c_s_f_using_metric_engine = me.evaluate_array()




#%%
