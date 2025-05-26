from lightstreamer import client
from trading_ig import IGService, IGStreamService
from datetime import datetime
import os
from queue import Queue
import requests
import time
import threading
import signal
import sys
from datetime import datetime, timedelta
import bisect

running = True

def signal_handler(sig, frame):
    global running
    print("\nShutting down gracefully...")
    running = False
    sys.exit(0)


def ig_stream_sample(epics):
    session = requests.Session()
    ig_service = IGService(
        "suerizz",
        "Suerizz123",
        "e051b8ba6512ef665fdd1a8d21b0412e5e55cf30",
        "LIVE",
        acc_number="RUUIL",
        session=session
    )
    ig_stream_service = IGStreamService(ig_service)
    ig_stream_service.create_session()
    items = [f"CHART:{epic}:TICK" for epic in epics]
    mode = "DISTINCT"
    fields = ["BID", "OFR", "UTM"]
    market_subscription = client.Subscription(mode=mode, items=items, fields=fields)
    market_listener = MarketListener(epics, ig_stream_service)
    market_subscription.addListener(market_listener)
    ig_stream_service.subscribe(market_subscription)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    while running:
        time.sleep(3600)

    ig_stream_service.disconnect()
    return market_listener

def create_folders(today_dt, instruments, parent_directory, n_days):
    folder_timestamps=[]
    folder_dates=[]
    for i in range(n_days + 1):
        folder_datetime = today_dt + timedelta(days=i) 
        folder_data_str = folder_datetime.strftime("%y-%m-%d")
        child_directory = os.path.join(parent_directory, folder_data_str)
        if not os.path.isdir(child_directory):
            os.makedirs(child_directory)
        
        for instrument in instruments:
            filename = os.path.join(child_directory, f"{instrument}.txt")
            if not os.path.exists(filename):
                open(filename, "w").close()

        folder_timestamp = folder_datetime.timestamp()
        folder_timestamps.append(folder_timestamp)
        folder_dates.append(folder_data_str)
    return folder_timestamps, folder_dates


class MarketListener(client.SubscriptionListener):
    def __init__(self, instrument_ids, ig_stream_service):
        super().__init__()
        self.instrument_ids = instrument_ids
        self.stream_service = ig_stream_service
        self.last_vals = {ins_id: [] for ins_id in instrument_ids}
        today_dt = datetime.now()
        self.today_str = today_dt.strftime("%y-%m-%d")
        self.buffered_prices = {instrument: [] for instrument in instrument_ids}
        self.last_update = time.time()
        self.save_queue = Queue()
        self.last_price_response = time.time()
        self.file_names = {}
    
        self.parent_directory = r"C:\Users\tedlo\Documents\python_scripts\live_price_chart\test_data"
        
        n_days = 5 - today_dt.weekday()
        
        self.folder_timestamps, self.folder_dates = create_folders(today_dt, instrument_ids, self.parent_directory, n_days)
        threading.Thread(target=self._save_worker, daemon=True).start()
        threading.Thread(target=self._response_checker, daemon=True).start()


    def _flush_buffers(self):
        """Force-write any remaining data before shutdown"""
        for instrument, buffered_prices in self.buffered_prices.items():
            with open(self.file_names[instrument], "a") as f:
                for t, bid, ask in buffered_prices:
                    f.write(f"{t},{bid},{ask}\n")
        self.buffered_prices = {instrument: [] for instrument in self.instrument_ids}

    def _response_checker(self):
        while True:
            if time.time() - self.last_price_response > 1 * 60:
                print("\nDisconnected\n")
                self._reconnect()
            time.sleep(3)

    def _reconnect(self):
        try:
            print("Attempting to disconnect...")
            self.stream_service.disconnect()
        except Exception:
            print(f"Could not disconnect")
            pass
        self.stream_service.create_session()
        items = [f"CHART:{epic}:TICK" for epic in self.instrument_ids]
        sub = client.Subscription(mode="DISTINCT", items=items, fields=["BID", "OFR", "UTM"])
        sub.addListener(self)
        self.stream_service.subscribe(sub)
        self.last_price_response = time.time()

    def onItemUpdate(self, update: client.ItemUpdate):
        epic_name = update.getItemName()
        _, instrument_id, _ = epic_name.split(':')
        bid_price = update.getValue(1)
        ask_price = update.getValue(2)
        timestamp = update.getValue(3)
        
        if isinstance(bid_price, str):
            bid_price = str(float(bid_price))
            timestamp = str(float(timestamp))
            self.last_price_response = time.time()
        else:
            bid_price = ""
        if isinstance(ask_price, str):
            ask_price = str(float(ask_price))
            timestamp = str(float(timestamp))
            self.last_price_response = time.time()
        else:
            ask_price = ""
        self.buffered_prices[instrument_id].append([timestamp, bid_price, ask_price])
        if time.time() - self.last_update > 5 * 60:
            self.last_update = time.time()
            buffered_copy = self.buffered_prices
            self.buffered_prices = {instrument: [] for instrument in self.instrument_ids}
            self.save_queue.put(buffered_copy)

    def _save_worker(self):
        while True:
            buffered_prices_dict = self.save_queue.get()
            today = datetime.now().strftime("%y-%m-%d")
            for instrument, buffered_prices in buffered_prices_dict.items():
                with open(f"{self.parent_directory}/{today}/{instrument}.txt", "a") as f:
                    for t, bid, ask in buffered_prices:
                        f.write(f"{t},{bid},{ask}\n")
            self.save_queue.task_done()




    def map_float_to_value(self, x: float):
        index = bisect.bisect_right(self.folder_timestamps, x) - 1
        return self.folder_dates[index]


if __name__ == "__main__":
    indice_epics = ["IX.D.SPTRD.IFA.IP",
        "IX.D.HANGSENG.IFA.IP",
        "CC.D.HG.UMA.IP",
        "IX.D.DAX.IFA.IP",
        "IX.D.STXE.IFM.IP",
        "IX.D.XINHUA.IFA.IP",
        "IX.D.AEX.IFD.IP",
        "IX.D.ASX.IFD.IP",
        "IX.D.CAC.IFD.IP",
        "IX.D.FTSE.CFD.IP",
        "IX.D.IBEX.IFD.IP",
        "IX.D.NASDAQ.IFD.IP",
        "IX.D.NIKKEI.IFD.IP",
        "IX.D.OMX.IFD.IP",
        "IX.D.SINGAPORE.IFD.IP",
        "IX.D.SMI.IFD.IP",
        "IX.D.TAIWAN.IFD.IP",
        ]
    fx_epics = ["CS.D.EURUSD.CFD.IP",
               "CS.D.GBPUSD.CFD.IP",
               "CS.D.GBPEUR.CFD.IP",
                "CS.D.USDCHF.CFD.IP",
                "CS.D.EURCHF.CFD.IP",
                "CS.D.USDJPY.CFD.IP",
                "CC.D.DX.UMA.IP",
                "CS.D.EURJPY.CFD.IP",
                ]
    epics = indice_epics + fx_epics    

    ig_stream_sample(epics)
