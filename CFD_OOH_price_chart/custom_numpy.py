#%%

from __future__ import annotations
from typing import List, Dict, Union, Tuple, Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from custom_numpy import BufferArray

import numpy as np
    
class BufferArray(np.ndarray):
    GROWTH = 2

    def __new__(cls, input_array):
        base = np.asarray(input_array, dtype=float)
        n    = base.size
        cap  = max(1, 2 * n)
        obj = super().__new__(cls, shape=(cap,), dtype=base.dtype)
        obj[:n]   = base
        obj[n:]   = np.nan
        obj.n = n
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.n = getattr(obj, "n", 0)
        
    def _grow(self):
        old = self.size
        self.resize(old * self.GROWTH, refcheck=False)
        self[old:] = np.nan
                            
    def append(self, value):
        if self.n >= self.size:
            self._grow()
        
        self[self.n] = value
        self.n += 1
        
    def get_last_value(self):
        if self.n > 0:
            return self[self.n-1]
        else:
            return self[0]
    
    def insert_value_at(self, value, n):
        self[n] = value
    
    def insert_values_between(self, values, n_l, n_h):
        self[n_l:n_h] = values
    
    def insert_values_leq(self, values, n):
        self[:n] = values

    def insert_values_geq(self, values, n):
        self[n:] = values

    def insert_last_value(self):
        self.append(self.get_last_value())
    
    def get_array(self):
        return self[:self.n]
        
    def get_array_at(self, lb, ub):
        return self[lb:ub]

        
    def to_numpy(self):
        return np.array(self.get_array())
    
    def min(self, axis=None, out=None, **kwargs):
        valid_data = self[:self.n].view(np.ndarray)
        return valid_data.min(axis=axis, out=out, **kwargs)

    def max(self, axis=None, out=None, **kwargs):
        valid_data = self[:self.n].view(np.ndarray)
        return valid_data.max(axis=axis, out=out, **kwargs)
   

arr_b = BufferArray(np.arange(10))



#%%
"""
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
TESTS
import numpy as np


def test_buffer_array():
    print("Creating initial BufferArray...")
    arr = BufferArray([1.0, 2.0, 3.0])
    assert arr.n == 3
    assert np.allclose(arr.get_array(), [1.0, 2.0, 3.0])
    assert np.isnan(arr[3:]).all()  # capacity > size

    print("Appending values...")
    arr.append(4.0)
    arr.append(5.0)
    arr.append(6.0)
    assert arr.n == 6
    assert np.allclose(arr.get_array(), [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])

    print("Testing auto-growing...")
    # Force a grow
    for _ in range(20):
        arr.append(10.0)
    assert arr.n == 26
    assert np.allclose(arr.get_array()[-3:], [10.0, 10.0, 10.0])

    print("Testing insert_last_value...")
    arr.insert_last_value()
    assert arr.n == 27
    assert arr.get_last_value() == 10.0

    print("Testing to_numpy...")
    np_arr = arr.to_numpy()
    assert isinstance(np_arr, np.ndarray)
    assert not isinstance(np_arr, BufferArray)
    assert np_arr.shape == (arr.n,)

    print("Testing insert_values (copy)...")
    other = BufferArray([100, 200, 300])
    arr.insert_values(other)
    assert np.allclose(arr[:3], [100, 200, 300])

    print("All tests passed.")

test_buffer_array()



"""