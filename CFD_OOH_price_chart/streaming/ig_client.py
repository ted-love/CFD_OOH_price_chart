from __future__ import annotations
from typing import Union, Dict, TYPE_CHECKING, List
if TYPE_CHECKING:
    from queue import Queue
    from trading_ig import IGStreamService

import trading_ig
import requests
from streaming import market_listener
from lightstreamer import client
from streaming import utils as utils_streaming

try:
    from streaming import credentials
except ImportError:
    raise ImportError("You need to create a credentials.py file. See credentials_template.py for an example.")


def get_tokens(username, api_key, password):
    response = requests.post(
        "https://api.ig.com/gateway/deal/session",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-IG-API-KEY": api_key,
            "Version": "1"
        },
        json={
            "identifier": username,
            "password": password
        }
    )
    
    return response.headers["X-SECURITY-TOKEN"], response.headers["CST"], 

def get_headers(username, api_key, password):
    response = requests.post(
        "https://api.ig.com/gateway/deal/session",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-IG-API-KEY": api_key,
            "Version": "1"
        },
        json={
            "identifier": username,
            "password": password
        }
    )
    return response


def create_streaming_application(capital_epics: List[str],
                                 queue_object: Queue
                                 ) -> IGStreamService:
    
    session = requests.Session()
    session.verify = False

    username, api_key, password, account_type, account_number = credentials.get_ig_credentials()
    
    stream_service = trading_ig.IGService(username,
                                        password,
                                        api_key,
                                        account_type,
                                        acc_number=account_number
                                        )
    ig_stream_service = trading_ig.IGStreamService(stream_service)
    ig_stream_service.create_session()
    
    mode, items, fields = utils_streaming.create_client_inputs(capital_epics)
    
    market_subscription = client.Subscription(mode=mode, items=items, fields=fields)


    listener = market_listener.MarketListener(queue_object)
    market_subscription.addListener(listener)
    ig_stream_service.subscribe(market_subscription)
    return ig_stream_service




