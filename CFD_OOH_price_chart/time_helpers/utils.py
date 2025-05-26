import pandas as pd
from datetime import datetime, time, timedelta, date
from typing import List, Dict, Callable, Optional, Any, Union
import numpy as np
import pytz

from datetime import datetime, time, timedelta, date
from typing import List, Tuple, Dict, Union
from . import classes as classes_time_helpers




def _find_closest_weekday(start_datetime, end_weekday, add_sub_function):
    for idx in range(7):
        datetime_i = add_sub_function(start_datetime, timedelta(days=idx))
        if datetime_i.weekday() == end_weekday:
            break
    return datetime_i


def _create_datetime_range(current_market_datetime: datetime,
                           n_points: int,
                           weekday_open_schedule: List[int],
                           weekday_closed_schedule: List[int]
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

def get_auction_period(open_time: Union[time, None],
                       auction_duration: Union[float, int]
                       ) -> Tuple[time, time]:
    auction_period_final=None
    if isinstance(auction_duration, (float, int)) and not open_time is None:
        if auction_duration > 0:
            auction_start_datetime = datetime.combine(datetime.now().date(), open_time) - timedelta(minutes=auction_duration)
            auction_start_time = auction_start_datetime.time()
            auction_period_final = (auction_start_time, open_time)
            
    return auction_period_final

def find_seasonal_trading_times(current_time: datetime,
                                timezone: str,
                                open_time: Dict[str, str],
                                close_time: Dict[str, str],
                                ) -> Tuple[time, time]:
    dst_offset = current_time.astimezone(pytz.timezone(timezone)).dst().total_seconds()
    if dst_offset == 0:
        open_time, close_time = open_time["st"], close_time["st"]
    else:
        open_time, close_time = open_time["dst"], close_time["dst"]

    open_time_final=None
    close_time_final=None
    
    if isinstance(open_time, str):
        open_time_final = time.fromisoformat(open_time)
    if isinstance(close_time, str):
        close_time_final = time.fromisoformat(close_time)
        
    return open_time_final, close_time_final

def find_current_trading_period(market_datetime: datetime,
                                market_status: bool,
                                open_periods: List[Dict[str, datetime]],
                                closed_periods: List[Dict[str, datetime]]
                                ) -> Dict[str, float]: 
    if market_status:
        periods = open_periods
    else:
        periods = closed_periods
    for p in periods:
        if p["start"] < market_datetime < p["end"]:
            current_period = p
            break
    return current_period


def get_most_recent_close_timestamp(timezone: str,
                                    closed_periods: List[Dict[str, datetime]],
                                    ) -> float:
    current_time_market_tz = classes_time_helpers.PatchedDateTime.now().astimezone(pytz.timezone(timezone))

    prev_close_datetime = closed_periods[0]["start"]
    for closed_period in closed_periods[1:]:
        if closed_period["start"] > current_time_market_tz:
            break
        else:
            prev_close_datetime = closed_period["start"]
    return prev_close_datetime.timestamp()
    

def create_open_periods(date_range: List[date],
                        weekday_open_schedule: List[int], 
                        holiday_schedule: Dict[date, Union[time, str]], 
                        open_time: time,
                        close_time: time
                        ) -> List[Dict[str, datetime]]:
    periods = []
    for d_date in date_range:
        if d_date.weekday() not in weekday_open_schedule:
            continue
        holiday_status = holiday_schedule.get(d_date)
        if holiday_status == "full":
            continue
            
        if holiday_status and holiday_status != "full":
            early_close = holiday_status
            if open_time < close_time:
                end_date, end_time = d_date, early_close
            else:
                end_date = d_date if early_close > close_time else d_date + timedelta(days=1)
                end_time = early_close if early_close > close_time else close_time
        else:
            end_date = d_date if open_time < close_time else d_date + timedelta(days=1)
            end_time = close_time

        start = datetime.combine(d_date, open_time)
        end = datetime.combine(end_date, end_time)
        date_dict = {"start" : start,
                     "end" : end}
        periods.append(date_dict)
    return periods

def create_closed_periods(open_periods: List[Dict[str, datetime]]
                          ) -> List[Dict[str, datetime]]:
    if not open_periods:
        return []
    sorted_periods = sorted(open_periods, key=lambda x: x['start'])
    return [{'start': sorted_periods[i-1]['end'], 'end': p['start']} for i, p in enumerate(sorted_periods) if i > 0 and sorted_periods[i-1]['end'] < p['start']]


def create_open_closed_periods(current_market_datetime: datetime,
                               n_points: int,
                               weekday_open_schedule: List[int],
                               weekday_closed_schedule: List[int],
                               open_time: time,
                               close_time: time,
                               ) -> List[List[Dict[str, datetime]]]:

    _date_range = _create_datetime_range(current_market_datetime,
                                         n_points,
                                         weekday_open_schedule,
                                         weekday_closed_schedule)
    open_periods = create_open_periods(_date_range,
                                       weekday_open_schedule,
                                       weekday_closed_schedule,
                                       open_time,
                                       close_time)
    closed_periods = create_closed_periods(open_periods)
    return open_periods, closed_periods


def check_if_currently_opened(current_market_datetime: datetime,
                              open_periods: List[Dict[str, datetime]],
                              closed_periods: List[Dict[str, datetime]]
                              ) -> bool: 
    for o_period, c_period in zip(open_periods, closed_periods):
        if o_period["start"] <= current_market_datetime < o_period["end"]:
            return True
        if c_period["start"] <= current_market_datetime < c_period["end"]:
            return False




def get_most_recent_close_timestamp(timezone: str,
                             closed_periods: List[Dict[str, datetime]],
                             ) -> float:
    current_time_market_tz = classes_time_helpers.PatchedDateTime.now().astimezone(pytz.timezone(timezone))

    prev_close_datetime = closed_periods[0]["start"]
    for closed_period in closed_periods[1:]:
        if closed_period["start"] > current_time_market_tz:
            break
        else:
            prev_close_datetime = closed_period["start"]
    return prev_close_datetime.timestamp()
    




def find_closest_points(current_market_datetime, market_tz, open_periods, closed_periods):
    current_market_datetime = current_market_datetime.replace(tzinfo=None)
    currently_open="unknown"
    
    for schedule in open_periods:
        if schedule[0] <= current_market_datetime < schedule[1]:
            currently_open=True
            closest_open_pre = schedule[0]
            closest_close_pre = schedule[1]
            closest_open = pd.Timestamp(closest_open_pre, tz=pytz.timezone(market_tz))
            closest_close = pd.Timestamp(closest_close_pre, tz=pytz.timezone(market_tz))
            break
        else:
            prev_close_pre = schedule[1]
            prev_close = pd.Timestamp(prev_close_pre, tz=pytz.timezone(market_tz))
    
    if currently_open == "unknown":
        for schedule in closed_periods:
            if schedule[0] <= current_market_datetime < schedule[1]:
                currently_open=False
                closest_open_pre = schedule[1]
                closest_close_pre = schedule[0]
                closest_open = pd.Timestamp(closest_open_pre, tz=pytz.timezone(market_tz))
                closest_close = pd.Timestamp(closest_close_pre, tz=pytz.timezone(market_tz))
                prev_close = pd.Timestamp(closest_close_pre, tz=pytz.timezone(market_tz))
                break
    return currently_open, closest_open, closest_close, prev_close


    
    




def tester():

    holiday_schedule = {datetime(2025, 5, 15).date() : "full",
                        datetime(2025, 5, 9).date() : time(12),
                        }

    date_range = [date(2025, 5, 1) + timedelta(days=i) for i in range(25)]

    weekday_open_schedule = [0, 1, 2, 3, 4] 
    open_time = time(2,15)
    close_time = time(22)

    periods_open = create_open_periods(date_range, weekday_open_schedule, holiday_schedule, open_time, close_time)
    periods_closed = create_closed_periods(periods_open)

    from pprint import pprint

    pprint(periods_closed)
