from datetime import datetime, timedelta
from typing import List, Dict



def set_datetime_param(test_flag: bool):
    datetime_now = datetime.now()
    datetime_delay = datetime(2025, 5, 21, 9)  # synthetic
    
    if test_flag:
        datetime_param = datetime_delay
    else:
        datetime_param = datetime_now
    
    sec_delay = (datetime_now - datetime_param).total_seconds()
    return sec_delay

# Initialize with default value (False)
sec_delay = set_datetime_param(False)

class PatchedDateTime(datetime):
    sec_delay = sec_delay
    
    @classmethod
    def now(cls, tz=None):
        return super().now(tz) - timedelta(seconds=cls.sec_delay)

class SystemClock:
    def __init__(self, minute_offset=None, specific_time=None):
        if not specific_time is None:
            minute_offset = (datetime.now() - specific_time).total_seconds() / 60
        if minute_offset is None:
            self.current_datetime_func = datetime.now
        else:
            self.current_datetime_func = lambda: datetime.now() - timedelta(minutes=minute_offset)
        
    def get_datetime_now(self):
        return self.current_datetime_func()
    
    
class MarketStatus:
    def __init__(self, ts: float, flag, dummy_flag=False):
        self.ts=ts
        self.flag=flag
        self.dummy_flag=dummy_flag

    def __call__(self, ts_i=None):
        if self.dummy_flag:
            return True
        else:
            if ts_i is None:
                ts_i = PatchedDateTime.now().timestamp()
            if self.flag:  
                return ts_i < self.ts 
            else: 
                return ts_i >= self.ts

def initialize_time_helpers(test_flag: bool):
    global sec_delay
    sec_delay = set_datetime_param(test_flag)
    PatchedDateTime.sec_delay = sec_delay