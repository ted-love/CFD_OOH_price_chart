from dataclasses import dataclass, field
from typing import Callable, Sequence, List, Dict, NoReturn, Union, Tuple, Any
from datetime import date, time



@dataclass(slots=True, kw_only=True, frozen=True)
class ExchangeInfo:
    name: str
    timezone: str
    weekday_open_schedule: List[int]
    weekday_closed_schedule: List[int]
    holiday_schedule: Dict[date, Union[time, str]]

