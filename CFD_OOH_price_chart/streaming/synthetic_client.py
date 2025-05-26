from __future__ import annotations
from typing import Union, Dict, TYPE_CHECKING, List
if TYPE_CHECKING:
    from queue import Queue
    from streaming.synthetic_websocket import SyntheticService

from streaming import synthetic_websocket
from streaming import market_listener
from streaming import utils as utils_streaming
import requests


def create_streaming_application(instrument_container: List[str],
                                 capital_epics: Dict[str, str],
                                queue_object: Queue,
                                ) -> SyntheticService:
    
    session = requests.Session()
    session.verify = False
    
    stream_service = synthetic_websocket.SyntheticService()
    stream_service.create_session()


    mode, items, fields = utils_streaming.create_client_inputs(instrument_container, capital_epics)
    market_subscription = synthetic_websocket.Subscription(mode=mode, items=items, fields=fields)

    listener = market_listener.MarketListener(queue_object)
    market_subscription.addListener(listener)
    stream_service.subscribe(market_subscription)
    return stream_service

