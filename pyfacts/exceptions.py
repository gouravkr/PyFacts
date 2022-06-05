import datetime
from typing import Literal


class DateNotFoundError(Exception):
    """Exception to be raised when date is not found"""

    def __init__(self, message, date):
        message = f"{message}: {date}"
        super().__init__(message)


class DateOutOfRangeError(Exception):
    """Exception to be raised when provided date is outside the range of dates in the time series"""

    def __init__(self, date: datetime.datetime, type: Literal['min', 'max']) -> None:
        if type == 'min':
            message = f"Provided date {date} is before the first date in the TimeSeries"
        if type == 'max':
            message = f"Provided date {date} is after the last date in the TimeSeries"
        super().__init__(message)
