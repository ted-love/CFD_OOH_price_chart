from __future__ import annotations
from typing import List, Dict, Union, Tuple, Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from instruments.classes import PriceInstrument, BaseInstrument
    from timeseries.classes import TimeSeries, ParentTimeSeries
    from .classes import SubPlotStructure

import pytz
from . import classes as classes_plot_config


from time_helpers import builders as builders_time_helpers
from time_helpers import classes as classes_time_helpers
from time_helpers import utils as utils_time_helpers


def create_subplot_structure_containers(plot_configs: Dict[str, Dict[str, str]],
                                        timeseries_parent_container: Dict[str, ParentTimeSeries],
                                        instrument_container: Dict[str, PriceInstrument],
                                        
                               ) -> Dict[str, SubPlotStructure]:
    plot_configs_dataclasses={}
    for name, config in plot_configs.items():
        focus_instrument = config["focus_instrument"]
        instrument_specs = instrument_container[focus_instrument].specs
        if not instrument_specs.close_time is None:
            current_time_market_tz = classes_time_helpers.PatchedDateTime.now().astimezone(pytz.timezone(instrument_specs.timezone))
            open_periods, closed_periods = builders_time_helpers.create_open_closed_periods(current_time_market_tz,
                                                                                            instrument_specs.timezone,
                                                                                            instrument_specs.holiday_schedule,
                                                                                            instrument_specs.weekday_open_schedule,
                                                                                            instrument_specs.weekday_closed_schedule,
                                                                                            instrument_specs.open_time,
                                                                                            instrument_specs.close_time,
                                                                                            14)
            
            most_recent_close_timestamp = utils_time_helpers.get_most_recent_close_timestamp(instrument_specs.timezone,
                                                                                             closed_periods)
            
            
            filtered_timeseries = {name : timseries for name, timseries in timeseries_parent_container.items() if name in config["instrument_names"]}
            filtered_instruments = {name : instrument_object for name, instrument_object in instrument_container.items() if name in config["instrument_names"]}
            config["instrument_names"]
            config["name"] = name
            config["close_point"] = most_recent_close_timestamp
            config["timeseries_parent_container"]=filtered_timeseries
            config["instrument_parent_container"]=filtered_instruments
            
            config_dataclass = classes_plot_config.SubPlotStructure(**config)
            plot_configs_dataclasses[name] = config_dataclass
    return plot_configs_dataclasses


def create_returns2(timeseries_parent_all: Dict[str, ParentTimeSeries],
                   plot_config_structure: Dict[str, SubPlotStructure],
                    ) -> None:
    for plot_config in plot_config_structure.values():
        timestamp=plot_config.close_point
        for instrument_name in plot_config.instrument_names:
            timeseries_parent = timeseries_parent_all[instrument_name]
            
            timeseries_child = timeseries_parent.create_child(timestamp, 
                                                              metric_type=plot_config.metric_attributes["metric_type_child"], 
                                                              metric_type_displayed_child=plot_config.metric_attributes["metric_type_displayed_child"], 
                                                              value_attr_parent=plot_config.metric_attributes["value_attr_parent"],
                                                              inclusion_flags=True)
            plot_config.add_timeseries(timeseries_child)
            
            
            
            