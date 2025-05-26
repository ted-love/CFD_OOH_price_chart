from __future__ import annotations
from datetime import time
import pytz
from typing import List, Dict, TYPE_CHECKING
from .info import info_utils
import numpy as np
import copy
from . import classes as classes_instruments
from exchanges.classes import ExchangeInfo
from utils import PatchedDateTime
from time_helpers import utils as utils_time_helpers
from time_helpers import builders as builders_time_helpers
from time_helpers.classes import PatchedDateTime
from time_helpers import classes as classes_time_helpers
from mathematics import numerics as math_numerics

if TYPE_CHECKING:
    from timeseries.classes import ParentTimeSeries
    from .classes import InstrumentSpecs, InstrumentInfo, PriceInstrument, InstrumentContainer, InstrumentContainer
    from subplot_structure.classes import SubPlotStructure



def _parse_breaks_str(breaks):
    if isinstance(breaks, list):
        break_intervals=[]
        for break_interval in breaks:
            t1, t2 = break_interval.split("-")
            interval = (time.fromisoformat(t1), time.fromisoformat(t2))
            break_intervals.append(interval)
    else:
        break_intervals=None
    return break_intervals


def create_instrument_info_classes(instrument_spec_container: Dict[str, InstrumentSpecs]
                                   ) -> Dict[str, InstrumentInfo]:
    instrument_info_container = {}
    for instrument, instrument_specs in instrument_spec_container.items():
        current_market_datetime = PatchedDateTime.now().astimezone(pytz.timezone(instrument_specs.timezone))
        
        args = [current_market_datetime,
                instrument_specs.timezone,
                instrument_specs.holiday_schedule,
                instrument_specs.weekday_open_schedule,
                instrument_specs.weekday_closed_schedule]
        time_args = [instrument_specs.open_time, instrument_specs.close_time]
        if not any(obj is None for obj in time_args):
            args = args + time_args + [14]
            open_periods, closed_periods = builders_time_helpers.create_open_closed_periods(*args)
            market_status_checker = builders_time_helpers.create_market_status_object(current_market_datetime, open_periods, closed_periods)
            current_period = utils_time_helpers.find_current_trading_period(current_market_datetime,
                                                                            market_status_checker(),
                                                                            open_periods,
                                                                            closed_periods)
            market_open = market_status_checker()
        else:
            market_open=True
            market_status_checker = classes_time_helpers.MarketStatus(None, None, True)
            current_period=None
        instrument_info = classes_instruments.InstrumentInfo(market_open=market_open,
                                                            check_market_status=market_status_checker,
                                                            current_period=current_period)

        instrument_info_container[instrument] = instrument_info
    return instrument_info_container

    
def create_instrument_spec_dataclasses(instrument_container: List[str],
                                                exchanges: Dict[str, ExchangeInfo]):
    instrument_info = info_utils.combine_and_get()

    instrument_info = instrument_info.loc[instrument_info.index.isin(instrument_container)]
    instrument_info.columns = [col.strip(" ") for col in instrument_info.columns]
    
    instrument_info_dict = instrument_info.to_dict(orient="index")
    
    instrument_info_dataclas_container = {}
    
    for name, inner_dict in instrument_info_dict.items():
        kwargs = {}
        
        for key, value in inner_dict.items():
            if not isinstance(value, str) and not value is None:
                if np.isnan(value):
                    inner_dict[key] = None
                
        open_time, close_time = utils_time_helpers.find_seasonal_trading_times(PatchedDateTime.now(),
                                                                               inner_dict["timezone"],
                                                                               open_time={"st" : inner_dict["open_time_st"], "dst" : inner_dict["open_time_dst"]},
                                                                               close_time={"st" : inner_dict["close_time_st"], "dst" : inner_dict["close_time_dst"]}
                                                                               )
        auction_period = utils_time_helpers.get_auction_period(open_time, inner_dict["auction_duration"])
        
        breaks = _parse_breaks_str(inner_dict["breaks"])

        exchange_obj = exchanges.get(inner_dict["exchange"], None)

        kwargs["name"] = name
        kwargs["asset_class"] = inner_dict["asset_class"]
        kwargs["exchange"] = inner_dict["exchange"]
        kwargs["auction_period"] = auction_period
        kwargs["timezone"] = inner_dict["timezone"]
        kwargs["open_time"] = open_time
        kwargs["close_time"] = close_time
        kwargs["breaks"] = breaks
        kwargs["weekday_open_schedule"] = eval(inner_dict["weekday_open_schedule"])
        kwargs["weekday_closed_schedule"] = eval(inner_dict["weekday_closed_schedule"])
        kwargs["holiday_schedule"] = exchange_obj.holiday_schedule if not exchange_obj is None else None
        instrument_info_dataclass = classes_instruments.InstrumentSpecs(**kwargs)
        instrument_info_dataclas_container[name] = instrument_info_dataclass
    return instrument_info_dataclas_container


def create_instrument_objects_objects(instrument_container: List[str],
                                    timeseries_parent_container: Dict[str, ParentTimeSeries],
                                    instrument_specs: Dict[str, InstrumentSpecs],
                                    instrument_info_container: Dict[str, InstrumentInfo],
                                    ) -> Dict[str, PriceInstrument]:
    base_objects={}
    for name in instrument_container:
        timeseries = timeseries_parent_container[name]
        specs = instrument_specs[name]
        instrument_info = instrument_info_container[name]
        base_instrument_object = classes_instruments.PriceInstrument(specs=specs,
                                                                    info=instrument_info,
                                                                    metric_type="price",
                                                                    timestamp=timeseries.timestamps[-1],
                                                                    bid=timeseries.bid[-1],
                                                                    ask=timeseries.ask[-1],
                                                                    display_name=specs.name)
        base_objects[name] = base_instrument_object
    return base_objects


