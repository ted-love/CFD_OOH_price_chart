import numpy as np
import operator
from types import MappingProxyType
import math
import ast
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import fields
from pprint import pformat



def get_epic_attr():
    return {
        "DE40":    {"tolerance": 0.0015},
        "EU50":    {"tolerance": 0.0015},
        "US500":   {"tolerance": 0.0015},
        "SW20":    {"tolerance": 0.0015},
        "UK100":   {"tolerance": 0.0015},
        "COPPER":  {"tolerance": 0.0015},
        "HK50":    {"tolerance": 0.002},
        "CN50":    {"tolerance": 0.002},
        "J225":    {"tolerance": 0.0015},
        "SG25":    {"tolerance": 0.0015},
        "default": {"tolerance": 9999999}
    }



def format_price(value):
    if abs(value) < 0.1:
        return f"{value:.2g}"
    else:
        return f"{value:.2f}"


def get_transformation_map(midPrice_at_close):
    transformation_map = {"price" : lambda x: x, 
                          "percentage" : lambda x : 100 * (x / midPrice_at_close - 1)
                          } 
    return transformation_map

def get_attribute_label_maps():
    metric_label_map = {"delta" : "Delta",
                        "ivol" : "Implied Volatility",
                        "IVOL_perc" : "Implied Volatility (%)",
                        "TVAR" : "Total Volatility",
                        "expiry" : "Expiry",
                        "years" : "Years",
                        "strike" : "Strike",
                        "moneyness" : "Moneyness (%)",
                        "log_moneyness" : "Log-Moneyness" ,
                        "standardised_moneyness" : "Standardised-Moneyness",
                        "price" : "Price", 
                        "percentage" : "Percentage",
                        }
    
    label_metric_map = {label : metric for metric, label in metric_label_map.items()}
    return metric_label_map, label_metric_map


def evaluate(expr, vars_dict):
    env = {
        "subtract": operator.sub,
        "add":      operator.add,
        "log":      np.log,
        "exp":      np.exp,
        "multiply": operator.mul,
        "divide":   operator.truediv,
    }
    return eval(expr, env, vars_dict)

_OP_MAP = MappingProxyType({
    'add'     : operator.add,
    'sub'     : operator.sub,
    'multiply': operator.mul,
    'truediv' : operator.truediv,
    'log'     : math.log,
    'exp'     : math.exp,
})


_ALLOWED_FUNCS = {
    "log":  math.log,
    "exp":  math.exp,
    "sqrt": math.sqrt,
}


def concat_data_tuples(data_tuples):
    df_frames=[]
    for d_tuple in data_tuples:
        df_i =  pd.DataFrame(d_tuple[2], index = d_tuple[1], columns=[d_tuple[0]])
        df_frames.append(df_i)

    df = pd.concat([df_i for df_i in df_frames], axis=1, ignore_index=False)
    df = df.sort_index()
    df = df.ffill(axis=0)
    df = df.dropna(axis=0)
    
    value_dict = df.to_dict(orient="list")
    value_dict = {key : np.array(values) for key, values in value_dict.items() if isinstance(values, list)}
    
    timestamps = df.index
    
    return timestamps, value_dict




def concat_price_dict2(data_dict):
    df_frames=[]
    cols = []
    for name, inner_dict in data_dict.items():
        df_i =  pd.DataFrame(inner_dict["y"], index = inner_dict["x"], columns=[name])
        df_frames.append(df_i)
        cols.append(name)
    df = pd.concat([df_i for df_i in df_frames], axis=1, ignore_index=False)
    df = df.sort_index()
    df = df.ffill(axis=0)
    df = df.dropna(axis=0)

    return df

def concat_price_series(data_dict):
    vals = []
    df_frames=[]
    cols = []
    for name, inner_dict in data_dict.items():
        df_i =  pd.DataFrame(inner_dict["y"], index = inner_dict["x"], columns=[name])
        df_frames.append(df_i)
        cols.append(name)
    df = pd.concat([df_i for df_i in df_frames], axis=1, ignore_index=False, )
    df = df.sort_index()
    df = df.ffill(axis=0)
    df = df.dropna(axis=0)
    res_dict={}
    
    for name in data_dict:
        ts = df.index
        values = df[name].values
        res_dict[name] = {"y" : values, "x" : ts} 
    return res_dict


def pprint_repr(cls):
    def __repr__(self):
        cls_name = self.__class__.__name__
        indent = ' ' * (len(cls_name) + 1)
        field_reprs = []
        for idx, field in enumerate(fields(self)):
            value = getattr(self, field.name)
            value_repr = pformat(value, width=80)
            lines = value_repr.split('\n')
            if len(lines) > 1:
                if idx == 0:
                    value_repr = '\n'.join([lines[0]] + [line for line in lines[1:]])
                else:
                    value_repr = '\n'.join([lines[0]] + [indent + line for line in lines[1:]])
            field_reprs.append(f"{field.name}={value_repr}")
        return f"{cls_name}(" + f",\n{indent}".join(field_reprs) + f"\n{' ' * len(cls_name)})"
    cls.__repr__ = __repr__
    return cls


import ast, math

_ALLOWED_FUNCS = {"log": np.log, "exp": np.exp, "sqrt": np.sqrt}

def _compile2(expr, extra=None):
    env = {**_ALLOWED_FUNCS, **(extra or {})}
    code = compile(ast.parse(expr, mode="eval"), "<expr>", "eval")
    return lambda d: eval(code, {"__builtins__": None, **env}, d)

def _compile(expr, extra=None):
    env = {**_ALLOWED_FUNCS, **(extra or {})}
    code = compile(ast.parse(expr, mode="eval"), "<expr>", "eval")
    return lambda d: eval(code, {"__builtins__": None, **env}, d)


def _vars(expr):
    tree = ast.parse(expr, mode="eval")
    ok, out = set(_ALLOWED_FUNCS), []
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and n.id not in ok and n.id not in out:
            out.append(n.id)
    return out

def _compiler_list(expr, extra=None):
    env = {**_ALLOWED_FUNCS, **(extra or {})}
    code = compile(ast.parse(expr, mode="eval"), "<expr>", "eval")
    variables = _vars(expr)
    def compiled_func(d=None, **kw):
        if isinstance(d, list):
            if len(d) != len(variables):
                raise ValueError(f"Expected {len(variables)} values, got {len(d)}")
            d = dict(zip(variables, d))
        local_vars = d or kw
        return eval(code, {"__builtins__": None, **env}, local_vars)
    return compiled_func

_METHODS = {"pct_change" : "100*(p2/p1-1)",
            "diff" : "p2-p1"}

def find_method(eval):
    for name, e in _METHODS.items():
        if e == eval:
            return name    
    raise NameError(f"No {eval} in _METHODS")

def find_instruments_from_expression(expr):
    all_instrument_names = list(epic_naming_map()[0].keys())
    instruments_in_operation = []
    n = len(expr)
    idx = 1
    for length in range(1, n + 1):
        for start in range(n - length + 1):
            instrument = expr[start:start + length]
            if instrument in all_instrument_names:
                instruments_in_operation.append(instrument)
                idx+=1
    return instruments_in_operation

def get_general_operation(operation_str, instrument_list):
    instrument_list = sorted(instrument_list, key=len, reverse=True)  # prioritize longest matches
    found = []
    remaining = operation_str
    general_operation = operation_str
    name_idx_map = {}
    idx_name_map = {}
    idx = 1
    n = len(instrument_list)

    for inst in instrument_list:
        pos = general_operation.find(inst)
        if pos != -1 and inst not in name_idx_map:
            name_idx_map[inst] = f"p{n+1 - idx}"
            idx_name_map[f"p{n+1 - idx}"] = inst
            
            general_operation = general_operation.replace(inst, f"p{n+1 - idx}")
            idx += 1
    general_operation = general_operation
    return general_operation, idx_name_map, name_idx_map



def find_operation(operation_str, instrument_list):
    instruments_in_operation = []
    n = len(operation_str)
    idx = 1
    general_operation = operation_str
    for length in range(1, n + 1):
        for start in range(n - length + 1):
            instrument = operation_str[start:start + length]
            if instrument in instrument_list:
                new_str = f"p{idx}"
                instruments_in_operation.append(instrument)
                general_operation = general_operation[:start] + new_str + general_operation[start + length:]
                idx+=1
    return instruments_in_operation, general_operation

class CustomOperation:
    def __init__(self, value_dict, op_expr):
        self.value_dict=value_dict
        self.op_expr=op_expr
        print(f"self.op_expr: {self.op_expr}")
        self.compiler = _compile(self.op_expr)
        self.value=self._evaluate()
        
    def update(self, instrument_name, value):
        self.value_dict[instrument_name]=value
        return self._evaluate()
        
    def _evaluate(self):
        return self.compiler(self.value_dict)
    
def calculate_grid_dims(n_plots):
    if n_plots == 0:
        return 0, 0
    if n_plots == 1:
        return 1, 1
    if n_plots == 2:
        return 1, 2
    if n_plots == 3:
        return 2, 2 
    if n_plots == 4:
        return 2, 2
    
    sqrt_n = np.sqrt(n_plots)
    nrows = int(np.floor(sqrt_n))
    ncols = int(np.ceil(sqrt_n))
    
    while nrows * ncols < n_plots:
        if ncols - nrows > 1:
            nrows += 1
        else:
            ncols += 1
    
    return nrows, ncols

def subplot_dimensions():
    plot_dims_map = {}
    plot_blank_map = {0 : 0}
    idx_map = {}
    for n in range(100):
        nrows, ncols = calculate_grid_dims(n)
        plot_dims_map[n] = nrows, ncols
        if nrows > 1:
            remainder = n % ncols 
            if remainder > 0:
                n_blanks = ncols - remainder
            else:
                n_blanks=0
        else:
            n_blanks=0
        if n == 3:
            n_blanks = 1
        plot_blank_map[n]=n_blanks
        idx = 0
        jdx = 0
        for ni in range(n):
            idx_map[ni] = (idx, jdx)
            if jdx == ncols-1:
                idx = 0 
                jdx += 1
            else:
                idx += 1
                
            
    return plot_dims_map, plot_blank_map, idx_map
