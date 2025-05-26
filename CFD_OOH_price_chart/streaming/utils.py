from instruments.info import info_utils




def create_client_inputs(capital_epics):
    capital_to_ig, _ = info_utils.epic_naming_map()
    ig_epics = [capital_to_ig[epic] for epic in capital_epics]

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
    
