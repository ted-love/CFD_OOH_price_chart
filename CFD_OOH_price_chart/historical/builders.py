import pandas as pd
import os
from typing import List, Dict
from . import utils as utils_historical

def retrieve_data(name_ig: str,
                  test_flag: bool,
                  ) -> pd.DataFrame:
    working_dir = os.getcwd()
    if test_flag:
        todays_folder_name = "todays_data_test"
    else:
        todays_folder_name = "todays_data"
    data_dir = os.path.join(working_dir, f"historical/data/{todays_folder_name}")
    directories = [d for d in os.listdir(data_dir)]
    dfs = []
    for d in directories:
        data_files = [fname for fname in os.listdir(f"{data_dir}/{d}") if os.path.isfile(os.path.join(f"{data_dir}/{d}", fname))]
        for file in data_files:
            if name_ig in file:
                data_file_for_epic = file
                break
        df = pd.read_csv(f"{data_dir}/{d}/{data_file_for_epic}", sep=",", header=None, names=["UTM","BID","OFR"]).dropna(how="all")
        df = df.dropna(how="all")
        if not df.empty:
            dfs.append(df)
    return pd.concat(dfs, ignore_index=False) if dfs else pd.DataFrame(columns=["UTM","BID","OFR"])

def get_historical_data(all_instruments: List[str],
                        capital_ig_map: Dict[str, str],
                        test_flag: bool,
                        ) -> Dict[str, pd.DataFrame]:
    df_dict={}
    for name_capital in all_instruments:
        name_ig = capital_ig_map[name_capital]
        df = retrieve_data(name_ig, test_flag) 
        df_cleaned = utils_historical.clean_data(df, test_flag)
        df_dict[name_capital]=df_cleaned
    return df_dict
