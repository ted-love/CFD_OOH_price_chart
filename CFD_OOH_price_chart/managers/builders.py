from __future__ import annotations
from typing import List, Dict, Union, Tuple, Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from instruments.classes import PriceInstrument, SyntheticInstrument
    from timeseries.classes import TimeSeries
    from managers.classes import GlobalInstrumentManager
    from .classes import SubPlotStructure, SeriesManager
from managers import classes as classes_managers
from datetime import datetime   


def create_base_series_managers(timeseries_all: Dict[str, TimeSeries],
                                instrument_objects_all: Dict[str, PriceInstrument]
                                ) -> Dict[str, SeriesManager]:
    series_managers_all = {}
    for name, instrument_obj in instrument_objects_all.items():
        timeseries = timeseries_all[name]
        
        series_manager = classes_managers.SeriesManager.create_from_objects([instrument_obj, timeseries],
                                                                            metric_type=instrument_obj.metric_type,
                                                                            timestamp_filters=datetime.now().timestamp())
        series_managers_all[name] = series_manager
    return series_managers_all