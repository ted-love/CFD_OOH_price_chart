import pandas as pd
import os
import re


def _read_csv(directory, file_name):
    df = pd.read_csv(os.path.join(directory, file_name), index_col="name")
    df.columns = df.columns.str.replace(r'\s+', '', regex=True)
    df.index = df.index.str.replace(r'\s+', '', regex=True)
    df.index.name = re.sub(r'\s+', '', df.index.name) if df.index.name else None
    df = df.map(lambda x: re.sub(r'\s+', '', x) if isinstance(x, str) else x)
    return df
    
def combine_and_get():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    forex = _read_csv(current_dir, "forex.csv")
    commodity = _read_csv(current_dir, "commodity.csv")
    index = _read_csv(current_dir, "index.csv")
    df = pd.concat([forex, commodity, index], axis=0)
    return df


def create_capital_ig_maps():
    df = combine_and_get()
    df = df.reset_index(drop=False)
    capital_ig_map = df.set_index("name").to_dict()["ig_name"]
    ig_capital_map = df.set_index("ig_name").to_dict()["name"]
 
    return capital_ig_map, ig_capital_map
