from __future__ import annotations
from typing import Set, Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from streaming.market_listener import MarketListener
    
import json
import asyncio
import websockets
from dataclasses import dataclass
import threading
from websockets.asyncio.client import connect
from time_helpers.classes import PatchedDateTime
from historical import utils


def get_data(names):
    data_dict = {}
    for name in names:
        df_i = utils.retrieve_data(name)        
        df_i["name"] = name
        df_i_filtered = df_i.loc[df_i["UTM"] > PatchedDateTime.now().timestamp() * 1000].copy()
        df_i_filtered.loc[df_i_filtered.index, "index_val"] = df_i_filtered["UTM"].values
        df_i_filtered = df_i_filtered.set_index("UTM", drop=True)
        df_i_filtered["UTM"] = df_i_filtered.index
        df_i_filtered = df_i_filtered.dropna(axis=0, how="any")
        df_i_filtered = df_i_filtered.astype(str)
        data_dict[name] = df_i_filtered.to_dict(orient="index")
        df_i_filtered
    return data_dict

        

class Websocket:
    def __init__(self, instrument_names):
        self.host = "localhost"
        self.port = 8765
        self.instrument_names=instrument_names
        self.uniform_var=0.001
        self.dt=1
        self._server = None
        self.data_dict = get_data(self.instrument_names)
        self.time_dilation = 1
        self.ms_to_s = 1/ 1000
        
        self.clients: Set[websockets.WebSocketServerProtocol] = set()

    def _get_sleep(self, value):
        return self.time_dilation * value * self.ms_to_s

    async def stop(self):
        for client in self.clients.copy():
            await client.close()
        self.clients.clear()

    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            print(f"Client disconnected: {websocket.remote_address}")
            self.clients.remove(websocket)

    async def broadcast_loop(self, instrument_name: str):
        data = self.data_dict[instrument_name]
        timestamps = list(data.keys())
        for i, (ts, data_message) in enumerate(data.items()):
            data_message["instrument"] = instrument_name
            for client in self.clients.copy():
                try:
                    await client.send(json.dumps(data_message))
                except websockets.exceptions.ConnectionClosed:
                    self.clients.remove(client)

            if i + 1 < len(timestamps):
                next_ts = timestamps[i + 1]
                delay_ms = next_ts - ts
                
                await asyncio.sleep(self._get_sleep(delay_ms))

    async def start_server(self):
        self._server = await websockets.serve(self.handler, self.host, self.port)

        while not self.clients:
            await asyncio.sleep(0.1)

        tasks = [asyncio.create_task(self.broadcast_loop(name)) for name in self.instrument_names]
        await asyncio.gather(*tasks)

        
    async def stop_server(self):
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
        for client in self.clients.copy():
            await client.close()
        self.clients.clear()


@dataclass(slots=True)
class ItemUpdate:
    name: str
    bid: str
    ask: str
    timestamp: str
    
    def update_values(self, ts, b, a):
        self.timestamp = ts
        self.bid = b
        self.ask = a
    
    def getItemName(self):
        return self.name
    
    def getValue(self, idx):
        if idx == 1:
            return self.bid
        elif idx == 2:
            return self.ask
        else:
            return self.timestamp

def get_item_name_map(items):
    item_name_map = {}
    for item in items:
        _, name, _ = item.split(":")
        item_name_map[item]=name
    return item_name_map

class Subscription:    
    def __init__(self, mode=None, items=None, fields=None):
        self.mode = mode
        self.items = items
        self.fields = fields
        self.ig_epics=None
        self.item_name_map=get_item_name_map(items)
        
        self.instrument_names = list(self.item_name_map.values()) 
        self.item_update_objects={self.item_name_map[item] : ItemUpdate(item, "", "", "") for item in items}
         
    def addListener(self, listener: MarketListener):
        self.listener=listener

    async def start_websocket(self):
        self.server = Websocket(self.instrument_names)
        self.server_task = asyncio.create_task(self.server.start_server())
                        
        async with connect(f"ws://localhost:8765") as self.websocket_client:
            loop = asyncio.get_event_loop()
            loop.create_task(self.ws_operation())
            
            while True:
                try:
                    message: bytes = await self.websocket_client.recv()
                except websockets.ConnectionClosed as e:
                    if not isinstance(e, websockets.exceptions.ConnectionClosedOK):
                        print(f"Connection closed with error: {e}")
                    break
                    
                data: Dict = json.loads(message)
                instrument = data["instrument"]
                item_object = self.item_update_objects[instrument]
                item_object.update_values(data["UTM"], data["BID"], data["OFR"])
                self.listener.onItemUpdate(item_object)
                
    async def ws_operation(self,) -> None:
        await self.websocket_client.send(json.dumps({"some": "message"}))
        
    async def stop(self):
        if self.server_task:
            await self.server.stop_server()
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
        if self.websocket_client:
            await self.websocket_client.close()
        


class SyntheticService:
    def __init__(self):
        self.subscription=None
        pass
    
    def create_session(self):
        pass
    
    def disconnect(self):
        if self.subscription:
            asyncio.run_coroutine_threadsafe(self.subscription.stop(), self.loop).result()
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)

    def subscribe(self, subscription: Subscription):
        self.subscription = subscription
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self._run_async, daemon=True)
        self.loop_thread.start()

    def _run_async(self):
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.subscription.start_websocket())
        self.loop.run_forever()

