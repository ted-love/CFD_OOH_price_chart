Create the conda environment by cd-ing to /CFD_OOH_price_chart/ then executing
```BASH
conda env create -f environment.yaml
```

To use the synthetic test, in main.py, set `test_flag=True` and in `utils.py` set 
```python 
# utils.py
delay_datetime = datetime(2025, 5, 6, 9)
```
For real-time, set

```python 
# utils.py
delay_datetime = datetime_now 
```

To change window configurations, go to `subplot_structure/config.py` and create a dictionary variable for each subplot.
In other words, if you want 5 subplots, you will need 5 map variables e.g. 
```python
map1 = {"name" : ...,
        "instrument_names" : ...,
        ...}
map2 = {"name" : ...}
...
```
In the example below, `"name"` is the subplot title, `"instrument_names"` to be plotted as in instrument names and the close time of the `"focus_instrument"` is the time the chart will start at.

```python
# subplot_structure/config.py
def _get_maps():

    eurex_map = {"name" : "EUREX",
                 "instrument_names" : ["DE40", "EU50", "US500", "UK100", "EURUSD", "COPPER"],
                "focus_instrument" : "DE40"
                }
    # other maps for other subplots e.g. ASIA 
```
