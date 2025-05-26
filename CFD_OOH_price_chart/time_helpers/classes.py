from datetime import datetime, timedelta
from typing import List, Dict


"""

for live-time set secs=0

"""

secs = (datetime.now() - datetime(2025, 5, 21, 8, 30)).total_seconds()
#secs=0
class PatchedDateTime(datetime):
    secs=secs
    
    @classmethod
    def now(cls, tz=None):
        return super().now(tz) - timedelta(seconds=cls.secs)

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
