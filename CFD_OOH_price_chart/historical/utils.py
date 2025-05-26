from instruments.info import info_utils
import pandas as pd
import os
from typing import List, Dict
from time_helpers.classes import PatchedDateTime

def retrieve_data(instrument_name: str,
                  ) -> pd.DataFrame:
    capital_to_IG, _ = info_utils.epic_naming_map()
    if instrument_name in capital_to_IG:
        instrument_name = capital_to_IG[instrument_name]
    working_dir = os.getcwd()
    data_dir = os.path.join(working_dir, f"historical/data/todays_data")
    directories = [d for d in os.listdir(data_dir)]
    dfs = []
    for d in directories:
        data_files = [fname for fname in os.listdir(f"{data_dir}/{d}") if os.path.isfile(os.path.join(f"{data_dir}/{d}", fname))]
        for file in data_files:
            if instrument_name in file:
                data_file_for_epic = file
                break
        df = pd.read_csv(f"{data_dir}/{d}/{data_file_for_epic}", sep=",", header=None, names=["UTM","BID","OFR"]).dropna(how="all")
        df = df.dropna(how="all")
        if not df.empty:
            dfs.append(df)
    return pd.concat(dfs, ignore_index=False) if dfs else pd.DataFrame(columns=["UTM","BID","OFR"])

def get_historical_data(all_instruments: List[str],
                        test_flag: bool,
                        ) -> Dict[str, pd.DataFrame]:
    df_dict={}
    for instrument_name in all_instruments:
        df = retrieve_data(instrument_name)
        df_cleaned = clean_data(df, test_flag)
        df_dict[instrument_name]=df_cleaned
    return df_dict

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


