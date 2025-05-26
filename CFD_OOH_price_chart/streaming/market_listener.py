from lightstreamer import client
from typing import Union, Dict, TYPE_CHECKING, List
from queue import Queue
from instruments.info import info_utils



class MarketListener(client.SubscriptionListener):
    def __init__(self, q: Queue):
        super().__init__()
        self.capital_to_ig, self.ig_to_capital = info_utils.epic_naming_map()
        self.temp_dict = {}
        self.q = q

    def onItemUpdate(self, update: client.ItemUpdate):
        epic_name =  update.getItemName()
        
        _, instrument_id, _ = epic_name.split(':')
        
        bid_price = update.getValue(1)
        ask_price = update.getValue(2)
        timestamp = update.getValue(3)

        if isinstance(bid_price, str):
            bid_price = float(bid_price)
            ask_price = float(ask_price)
            timestamp = float(timestamp)
            timestamp = timestamp / 1000

            capital_epic = self.ig_to_capital[instrument_id]
                
            self.q.put((capital_epic, timestamp, bid_price, ask_price))
            
 