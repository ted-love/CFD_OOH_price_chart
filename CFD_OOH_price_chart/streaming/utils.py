from instruments.info import info_utils


def create_client_inputs(instrument_list,
                         capital_ig_map):

    ig_epics = [capital_ig_map[epic] for epic in instrument_list]

    items = [f"MARKET:{epic}" for epic in ig_epics]
    fields=["UPDATE_TIME",
            "BID",
            "OFFER",
            "HIGH",
            "LOW",]
    mode = "MERGE"
    
    items = [f"CHART:{epic}:TICK" for epic in ig_epics]
    mode = "DISTINCT" 
    fields = ["BID", "OFR", "UTM"]
    
    return mode, items, fields
    
