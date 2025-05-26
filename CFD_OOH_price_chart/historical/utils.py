import pandas as pd
import os
from typing import List, Dict
from time_helpers.classes import PatchedDateTime

def clean_data(df: pd.DataFrame,
               test_flag: bool,
               ) -> Dict[str, pd.DataFrame]:
    df = df.drop_duplicates(subset=["UTM"], keep="first")
    df = df.sort_values(by=["UTM"])
    
    df = df.rename(columns={"UTM" : "timestamp",
                            "BID" : "bid",
                            "OFR" : "ask"})
    
    df["timestamp"] = df["timestamp"] / 1000
    df = df.set_index("timestamp", drop=True)
    df = df.dropna(axis=0)
    
    df[["bid", "ask"]] = df[["bid", "ask"]].ffill()
        
    mask = df.notna().all(axis=1)
    
    first_good = mask.idxmax()   
    df = df.loc[first_good :]
    if test_flag:
        df = df.loc[df.index <= PatchedDateTime.now().timestamp()]
    return df


