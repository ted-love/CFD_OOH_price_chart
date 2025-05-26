import numpy as np
from collections import defaultdict

def _get_plot_metric_attributes():
    attributes = {"major" : "price",
                  "minor" : "spread",
                  "value_attr_parent" : "mid",
                  "scale" : "pct"
                  }
    return attributes

def _get_maps():

    eurex_map = {"name" : "EUREX",
                 "instrument_names" : ["DE40", "EU50", "US500", "UK100", "EURUSD", "COPPER"],
                "focus_instrument" : "DE40"
                }
    
    swiss_map = {"name" : "SWISS",
                 "instrument_names" : ["DE40", "EU50", "US500", "SW20", "UK100", "EURUSD", "COPPER"],
                "focus_instrument" : "SW20"
                }
    
    FTSE_map = {"name" : "FTSE",
                 "instrument_names" : ["DE40", "EU50", "US500", "UK100", "GBPUSD", "COPPER"],
                "focus_instrument" : "UK100"
                }

    
    hkex_map = {"name" : "HKEX",
                 "instrument_names" : ["HK50", "US500", "CN50", "SG25", "J225", "TWN", "COPPER"],
                 "focus_instrument" : "HK50"
                }
    
    sgx_map = {"name" : "SGX",
                 "instrument_names" : ["HK50", "US500", "CN50", "SG25", "J225", "TWN", "COPPER"],
                 "focus_instrument" : "CN50"
                }
    
    
    asia_map = {"name" : "ASIA",
                  "instrument_names" : ["HK50", "CN50", "US500"],
                "focus_instrument" : "HK50"
                }
    
    aus_map = {"name" : "ASX",
                  "instrument_names" : ["AU200", "US500"],
                "focus_instrument" : "AU200"
                }
    
    sea_map = {"name" : "SEA",
                "instrument_names" : ["CN50", "US500", "TWN"],
                "focus_instrument" : "CN50"
                }

    all_maps = [d for d in locals().values() if isinstance(d, dict) and "name" in d]

    for d in all_maps:
        d["metric_attributes"] = _get_plot_metric_attributes()

    plot_maps = {d["name"]: d for d in all_maps}    
    return plot_maps

def get_config():
    plot_maps = _get_maps()

    total_instruments = []
    for d in plot_maps.values():
        for instrument in d["instrument_names"]:
            if not instrument in total_instruments:
                total_instruments.append(instrument)    
            
    return plot_maps, total_instruments


def get_exchange_params():
    CME_map = {"name" : "CME",
                 #"instrument_names" : ["DE40", "EU50", "US500", "SW20", "EURUSD", "EURCHF", "COPPER"],
                  "close_time_st" : "16:00",
                  "close_time_dst" : "16:00",
                  "open_time_st" : "17:00",
                  "open_time_dst" : "17:00",
                  "breaks" : [],
                  "timezone" : "America/Chicago",
                  "weekday_open_schedule" : [6, 0, 1, 2, 3],
                  "weekday_closed_schedule" : np.arange(5, dtype=int).tolist(),
                 }
    jpx_map = {"name" : "JPX",
                 #"instrument_names" : ["DE40", "EU50", "US500", "SW20", "EURUSD", "EURCHF", "COPPER"],
                  "close_time_st" : "06:00",
                  "close_time_dst" : "06:00",
                  "open_time_st" : "8:45",
                  "open_time_dst" : "8:45",
                  "timezone" : "Asia/Tokyo",
                  "breaks" : ["15:45-17:00"],
                  "weekday_open_schedule" : np.arange(5, dtype=int).tolist(),
                  "weekday_closed_schedule" : np.arange(5, dtype=int).tolist(),
                 }

    
    ice_map = {"name" : "ICE",
                 #"instrument_names" : ["DE40", "EU50", "US500", "SW20", "EURUSD", "EURCHF", "COPPER"],
                  "close_time_st" : "21:00",
                  "close_time_dst" : "21:00",
                  "open_time_st" : "01:00",
                  "open_time_dst" : "01:00",
                  "breaks" : [],
                  "timezone" : "Europe/London",
                  "weekday_open_schedule" : np.arange(5, dtype=int).tolist(),
                  "weekday_closed_schedule" : np.arange(5, dtype=int).tolist(),
              #    #"last_closed_weekday" : 4,
                  #"first_closed_weekday" : 0,
                  #"default_operations" : [],
                 }
    

    nasdaq_AB_map = {"name" : "NASDAQ AB",
                 #"instrument_names" : ["DE40", "EU50", "US500", "SW20", "EURUSD", "EURCHF", "COPPER"],
                  "close_time_st" : "17:25",
                  "close_time_dst" : "17:25",
                  "open_time_st" : "09:00",
                  "open_time_dst" : "09:00",
                  "breaks" : [],
                  "timezone" : "Europe/Berlin",
                  "weekday_closed_schedule" : np.arange(5, dtype=int).tolist(),
                  "weekday_open_schedule" : np.arange(5, dtype=int).tolist(),
              #    #"last_closed_weekday" : 4,
                  #"first_closed_weekday" : 0,
                  #"default_operations" : [],
                 }
    
    swiss_map = {"name" : "SWISS",
                 #"instrument_names" : ["DE40", "EU50", "US500", "SW20", "EURUSD", "EURCHF", "COPPER"],
                  "close_time_st" : "17:30",
                  "close_time_dst" : "17:30",
                  "open_time_st" : "08:50",
                  
                  "open_time_dst" : "08:50",
                  "breaks" : [],
                  "timezone" : "Europe/Berlin",
                  "weekday_closed_schedule" : np.arange(5, dtype=int).tolist(),
              #    #"last_closed_weekday" : 4,
                  #"first_closed_weekday" : 0,
                  #"default_operations" : [],
                 }
    
    
    eurex_map = {"name" : "EUREX",
                  #"instrument_names" : ["DE40", "EU50", "US500", "SW20", "UK100", "EURUSD", "DXY", "COPPER"],
                  "close_time_dst" : "22:00",
                  "open_time_dst" : "02:15",
                   "close_time_st" : "22:00",
                  "open_time_st" : "01:15",
                  "breaks" : [],
                  "timezone" : "Europe/Berlin",
                  #"last_closed_weekday" : 4,
                  #"first_closed_weekday" : 0,
                  "weekday_closed_schedule" : np.arange(5, dtype=int).tolist(),
                   "weekday_open_schedule" : np.arange(5, dtype=int).tolist(),
                  #"default_operations" : ["DE40-US500"],
                  }
    
    hkex_map = {"name" : "HKEX",
                #"instrument_names" : ["HK50", "US500", "CN50", "J225", "SG25", "COPPER"],
                "close_time_st" : "03:00",
                "close_time_dst" : "03:00",
                 "open_time_st" : "09:15",
                 "open_time_dst" : "09:15",
                 "breaks" : ["12:00-13:00", "16:30-17:15"],
                "timezone" : "Asia/Hong_Kong",
                #"last_closed_weekday" : 5,
                #"first_closed_weekday" : 0,
                "weekday_closed_schedule" : np.arange(1, 6, dtype=int).tolist(),
                 "weekday_open_schedule" : np.arange(5, dtype=int).tolist(),
                #"default_operations" : ["HK50-CN50"],
                }

    sgx_map = {#"instrument_names" : ["CN50", "SG25", "TWN", "J225", "US500"],
        
                
                "name" : "SGX",
                "close_time_st" : "05:15",
                "close_time_dst" : "05:15",
                 "open_time_st" : "09:00",
                 "open_time_dst" : "09:00",
                 "breaks" : ["17:20-17:50"],
                "timezone" : "Asia/Hong_Kong",
                #"first_closed_weekday" : 0,
                #"last_closed_weekday" : 5,
                "weekday_closed_schedule" : np.arange(1, 6, dtype=int).tolist(),
                 "weekday_open_schedule" : np.arange(5, dtype=int).tolist(),
                #"default_operations" : ["US500-CN50"],
                }

    market_params = [eurex_map, hkex_map, sgx_map, CME_map, nasdaq_AB_map, ice_map,jpx_map]
    """
    for market in market_params:
        holiday_schedule = _get_holiday_schedule(market["name"])
        market["holiday_schedule"]=holiday_schedule
    """
    return market_params






def get_params():
    swiss_map = {#"instrument_names" : ["DE40", "EU50", "US500", "SW20", "EURUSD", "EURCHF", "COPPER"],
                  "close_time" : "17:30",
                  "open_time" : "08:50",
                  "timezone" : "EUREX/Berlin",
                  "weekday_closed_schedule" : np.arange(5, dtype=int).tolist(),
              #    #"last_closed_weekday" : 4,
                  #"first_closed_weekday" : 0,
                  #"default_operations" : [],
                  "holiday_schedule" : [],
                 }
    
    eurex_map = {
                  #"instrument_names" : ["DE40", "EU50", "US500", "SW20", "UK100", "EURUSD", "DXY", "COPPER"],
                  "close_time" : "22:00",
                  "open_time" : "02:15",
                  "timezone" : "EUREX/Berlin",
                  #"last_closed_weekday" : 4,
                  #"first_closed_weekday" : 0,
                  "weekday_closed_schedule" : np.arange(5, dtype=int).tolist(),
                  #"default_operations" : ["DE40-US500"],
                  "holiday_schedule" : [],
                  }
    
    hkex_map = {#"instrument_names" : ["HK50", "US500", "CN50", "J225", "SG25", "COPPER"],
                "close_time" : "03:00",
                 "open_time" : "09:15",
                "timezone" : "Asia/Hong_Kong",
                #"last_closed_weekday" : 5,
                #"first_closed_weekday" : 0,
                "weekday_closed_schedule" : np.arange(1, 6, dtype=int).tolist(),
                #"default_operations" : ["HK50-CN50"],
                  "holiday_schedule" : [],
                }

    sgx_map = {#"instrument_names" : ["CN50", "SG25", "TWN", "J225", "US500"],
                "close_time" : "05:15",
                 "open_time" : "09:00",
                "timezone" : "Asia/Hong_Kong",
                #"first_closed_weekday" : 0,
                #"last_closed_weekday" : 5,
                "weekday_closed_schedule" : np.arange(1, 6, dtype=int).tolist(),
                #"default_operations" : ["US500-CN50"],
                  "holiday_schedule" : [],
                }

    market_maps = {"EUREX" : eurex_map,
                   "HKEX" : hkex_map,
                   "SWISS" : swiss_map,
                   "SGX" : sgx_map}

    epic_region_map = defaultdict(list)

    for region, region_map in market_maps.items():
        for epic in region_map["instrument_names"]:
            epic_region_map[epic].append(region)
            
    epic_region_map = dict(epic_region_map)
    plot_maps = {"market_maps" : market_maps,
                 "epic_region_map" : epic_region_map}
    
    return plot_maps


def get_colours():
    return ["yellow", "lime", "cyan", "blue", "orange", "purple", "pink", "magenta", "brown",
            "lightgray", "darkgray", "dimgray",
            "lightred", "darkred",
            "lightgreen", "darkgreen", "lime", "limegreen",
            "lightblue", "darkblue", "navy",
            "lightcyan", "darkcyan", "teal",
            "lightmagenta", "darkmagenta", "fuchsia",
            "lightyellow", "darkyellow", "gold", "goldenrod", "khaki",
            "lightpink", "darkpink", "hotpink",
            "lightsalmon", "darksalmon", "coral",
            "lightgoldenrod", "darkgoldenrod",
            ]      


def get_test_params():
    eurex_map = {
                  #"instrument_names" : ["DE40"],
                  "close_time" : "22:00",
                  "open_time" : "02:15",
                  "timezone" : "EUREX/Berlin",
                  "weekday_closed_schedule" : np.arange(5, dtype=int).tolist(),
                  #"last_closed_weekday" : 4,
                  #"first_closed_weekday" : 0,
                  #"default_operations" : [],
                  "holiday_schedule" : [],
   #               #"default_operations" : ["DE40-US500"]
                  }
    market_maps = {"EUREX" : eurex_map,
                    }

    epic_region_map = defaultdict(list)

    for region, region_map in market_maps.items():
        for epic in region_map["instrument_names"]:
            epic_region_map[epic].append(region)
            
    epic_region_map = dict(epic_region_map)
    plot_maps = {"market_maps" : market_maps,
                 "epic_region_map" : epic_region_map}
    
    return plot_maps


