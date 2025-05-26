
def get_config():
    
    tolerance_configs = {"dt" : 0.3,
                         "dw" : 0.2,
                         "adjustment" : 10}
    
    rounding_configs = {"weight" : 5}
    
    eurex_roles_configs = {"leader_instruments" : ["US500"],
                            "follower_instruments" :["DE40", "EU50"]
                            }
    swiss_roles_configs = {"leader_instruments" : ["US500", "EU50"],
                           "follower_instruments" :["SW20"]
                           }
    
    ftse_roles_configs = {"leader_instruments" : ["US500"],
                           "follower_instruments" :["UK100"]
                           }

    eurex_configs = {"tolerance" : tolerance_configs,
               "rounding" : rounding_configs,
               "instrument_roles_configs" : eurex_roles_configs}
    
    swiss_configs = {"tolerance" : tolerance_configs,
               "rounding" : rounding_configs,
               "instrument_roles_configs" : swiss_roles_configs}
    ftse_configs = {"tolerance" : tolerance_configs,
               "rounding" : rounding_configs,
               "instrument_roles_configs" : ftse_roles_configs}


    configs = {"EUREX" : eurex_configs,
               "SWISS" : swiss_configs,
               "FTSE" : ftse_configs}
    
  #  configs={}
    
    return configs