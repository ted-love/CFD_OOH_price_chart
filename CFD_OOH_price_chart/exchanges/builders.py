import os 
import pandas as pd
from datetime import time
from . import classes





def get_exchanges():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    info_dir = os.path.join(current_dir, "info")
    exchanges = [d for d in os.listdir(info_dir) if os.path.isdir(os.path.join(info_dir, d))]
    if "__pycache__" in exchanges:
        exchanges.remove("__pycache__")
    return exchanges

def create_exchange_objects():
    exchanges_all = get_exchanges()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    info_dir = os.path.join(current_dir, "info")
    
    exchange_dataclasses={}
    for exchange in exchanges_all:
        exchange_dir = os.path.join(info_dir, exchange)
        holiday_dir = os.path.join(exchange_dir, "holiday_schedule.csv")
        if os.path.exists(holiday_dir):
            holiday_schedule = pd.read_csv(holiday_dir, index_col="date")
            holiday_schedule.index = pd.to_datetime(holiday_schedule.index).date
            holiday_schedule["type"] = [s.strip(" ") for s in holiday_schedule["type"]]
            
            holiday_schedule["type"] = [time.fromisoformat(t) if t != "full" else t for t in holiday_schedule["type"].values]
            holiday_schedule = holiday_schedule.to_dict()["type"]
        else:
            holiday_schedule = {}
        metadata_dir = os.path.join(exchange_dir, "metadata.csv")
        if os.path.exists(metadata_dir):
            metadata = pd.read_csv(metadata_dir)
            metadata = metadata.to_dict(orient="index")[0]
            metadata["weekday_open_schedule"] = eval(metadata["weekday_open_schedule"])
            metadata["weekday_closed_schedule"] = eval(metadata["weekday_closed_schedule"])

        else:
            metadata = {"name" : exchange,
                        "timezone" : "",
                        "weekday_open_schedule" : [],
                        "weekday_closed_schedule" : []}
        
        metadata["holiday_schedule"] = holiday_schedule

        exchange_dataclass = classes.ExchangeInfo(**metadata)
        exchange_dataclasses[exchange] = exchange_dataclass
        
    return exchange_dataclasses
