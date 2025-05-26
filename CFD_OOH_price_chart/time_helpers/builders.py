import pandas as pd
from datetime import datetime, time, timedelta, date
from typing import List, Dict
import numpy as np
import pytz
from datetime import datetime, time, timedelta, date
from typing import List, Dict, Union
from . import utils as utils_time_helpers
from . import classes as classes_time_helpers



def _find_closest_weekday(start_datetime, end_weekday, add_sub_function):
    for idx in range(7):
        datetime_i = add_sub_function(start_datetime, timedelta(days=idx))
        if datetime_i.weekday() == end_weekday:
            break
    return datetime_i


def _create_datetime_range(current_market_datetime: datetime,
                           weekday_open_schedule: List[int],
                           weekday_closed_schedule: List[int],
                           n_points: int,
                           ) -> List[date]:
    schedule_min_temp = current_market_datetime.date() - timedelta(days=n_points)
    schedule_max_temp = current_market_datetime.date() + timedelta(days=n_points)
    
    
    datetime_range_lower = _find_closest_weekday(schedule_min_temp, weekday_closed_schedule, np.subtract)
    datetime_range_upper = _find_closest_weekday(schedule_max_temp, weekday_open_schedule, np.add)
    
    datetime_range=[]
    for idx in range(99999): 
        date_i = datetime_range_lower + timedelta(days=idx)
        datetime_range.append(date_i)
        if date_i == datetime_range_upper:
            break
    return datetime_range


def create_open_periods(date_range: List[date],
                        market_tz: str,
                        holiday_schedule: Dict[date, Union[time, str]], 
                        weekday_open_schedule: List[int], 
                        open_time: time,
                        close_time: time
                        ) -> List[Dict[str, datetime]]:
    periods = []
    
    for d_date in date_range:
        if d_date.weekday() not in weekday_open_schedule:
            continue
        
        holiday_status = holiday_schedule.get(d_date)
        
        if holiday_status is None:
            end_date = d_date if open_time < close_time else d_date + timedelta(days=1)
            end_time = close_time
        else:
            if holiday_status == "full":
                continue
            else:
                early_close = holiday_status
                if open_time < close_time:
                    end_date, end_time = d_date, early_close
                else:
                    end_date = d_date if early_close > close_time else d_date + timedelta(days=1)
                    end_time = early_close if early_close > close_time else close_time


        start = pd.Timestamp(datetime.combine(d_date, open_time), tz=pytz.timezone(market_tz))
        end = pd.Timestamp(datetime.combine(end_date, end_time), tz=pytz.timezone(market_tz))
        date_dict = {"start" : start,
                     "end" : end}
        periods.append(date_dict)
    return periods



def create_open_closed_periods(current_market_datetime: datetime,
                               market_tz: datetime,
                               holiday_schedule: Dict[date, Union[time, str]],
                               weekday_open_schedule: List[int],
                               weekday_closed_schedule: List[int],
                               open_time: time,
                               close_time: time,
                               n_points: int,
                               ) -> List[List[Dict[str, datetime]]]:

    _date_range = _create_datetime_range(current_market_datetime,
                                         weekday_open_schedule,
                                         weekday_closed_schedule,
                                         n_points)
    open_periods = create_open_periods(_date_range,
                                       market_tz,
                                       holiday_schedule, 
                                       
                                       weekday_open_schedule,
                                       open_time,
                                       close_time)
    closed_periods = create_closed_periods(open_periods)
    return open_periods, closed_periods





def create_closed_periods(open_periods: List[Dict[str, datetime]]
                          ) -> List[Dict[str, datetime]]:
    if not open_periods:
        return []
    sorted_periods = sorted(open_periods, key=lambda x: x['start'])
    return [{'start': sorted_periods[i-1]['end'], 'end': p['start']} for i, p in enumerate(sorted_periods) if i > 0 and sorted_periods[i-1]['end'] < p['start']]

def create_market_status_object(market_datetime: datetime,
                                open_periods: List[Dict[str, datetime]],
                                closed_periods: List[Dict[str, datetime]],
                                ) -> classes_time_helpers.MarketStatus:
        open_flag = utils_time_helpers.check_if_currently_opened(market_datetime, open_periods, closed_periods)
        if open_flag:
            periods = open_periods
        else:
            periods = closed_periods
        for p in periods:
            if p["start"] < market_datetime < p["end"]:
                next_event_timestamp = p["end"].timestamp()
        
        return classes_time_helpers.MarketStatus(next_event_timestamp, open_flag)

