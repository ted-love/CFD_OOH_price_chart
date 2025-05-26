import pandas as pd
import os

def combine_and_get():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    forex = pd.read_csv(os.path.join(current_dir, "forex.csv"), index_col="name")
    commodity = pd.read_csv(os.path.join(current_dir, "commodity.csv"), index_col="name")
    index = pd.read_csv(os.path.join(current_dir, "index.csv"), index_col="name")
    df = pd.concat([forex, commodity, index], axis=0)
    return df


def epic_naming_map():
    capital_to_IG = {"US500" : "IX.D.SPTRD.IFA.IP",
                     "HK50" : "IX.D.HANGSENG.IFA.IP",
                     "COPPER" : "CC.D.HG.UMA.IP",
                     "DE40" : "IX.D.DAX.IFA.IP",
                     "EU50" : "IX.D.STXE.IFM.IP",
                     "CN50" : "IX.D.XINHUA.IFA.IP",
                     "SW20" : "IX.D.SMI.IFD.IP",
                     "UK100" : "IX.D.FTSE.CFD.IP",
                     "OMX30" : "IX.D.OMX.CFD.IP",
                     "SP35" : "IX.D.IBEX.CFD.IP",
                     "AU200" : "IX.D.ASX.IFD.IP",
                     "J225" : "IX.D.NIKKEI.IFD.IP",
                     "TWN" : "IX.D.TAIWAN.IFD.IP",
                     "SG25" : "IX.D.SINGAPORE.IFD.IP",
                     "EURUSD" : "CS.D.EURUSD.CFD.IP",
                     "GBPUSD" : "CS.D.GBPUSD.CFD.IP",
                     "USDCHF" : "CS.D.USDCHF.CFD.IP",
                     "EURCHF" : "CS.D.EURCHF.CFD.IP",
                     "GBPEUR" : "CS.D.GBPEUR.CFD.IP",
                     "USDJPY" : "CS.D.USDJPY.CFD.IP",
                     "EURJPY" : "CS.D.EURJPY.CFD.IP",
                     "DXY" : "CC.D.DX.UMA.IP"
                     }
    
    IG_to_capital = {value : key for key, value in capital_to_IG.items()}
    return capital_to_IG, IG_to_capital
