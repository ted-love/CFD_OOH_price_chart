#%%
import numpy as np







hk = 20
us=10
new=15

value_dict = {"HK50" : hk, "US500" : us}
op_expr = "log(HK50/US500)"

co = CustomOperation(value_dict, op_expr)

print(f"CustomOperation: {co.update("US500", new)}")
print(f"Solution: {np.log(hk/new)}")
# %%
