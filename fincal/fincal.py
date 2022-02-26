from __future__ import annotations

import datetime
from typing import List, Literal, Union

from dateutil.relativedelta import relativedelta

from .core import AllFrequencies, TimeSeriesCore
from .utils import (
    _find_closest_date,
    _interval_to_years,
    _parse_date,
    _preprocess_match_options,
)


def create_date_series(
    start_date: datetime.datetime, end_date: datetime.datetime, frequency: str, eomonth: bool = False
) -> List[datetime.datetime]:
    """Creates a date series using a frequency"""

    frequency = getattr(AllFrequencies, frequency)
    if eomonth and frequency.days < AllFrequencies.M.days:
        raise ValueError(f"eomonth cannot be set to True if frequency is higher than {AllFrequencies.M.name}")

    start_date = _parse_date(start_date)
    end_date = _parse_date(end_date)
    datediff = (end_date - start_date).days / frequency.days + 1
    dates = []

    for i in range(0, int(datediff)):
        diff = {frequency.freq_type: frequency.value * i}
        date = start_date + relativedelta(**diff)
        if eomonth:
            if date.month == 12:
                date = date.replace(day=31)
            else:
                date = date.replace(day=1).replace(month=date.month+1) - relativedelta(days=1)
        if date <= end_date:
            dates.append(date)

    return dates


class TimeSeries(TimeSeriesCore):
    """Container for TimeSeries objects"""

    def info(self):
        """Summary info about the TimeSeries object"""

        total_dates = len(self.data.keys())
        res_string = "First date: {}\nLast date: {}\nNumber of rows: {}"
        return res_string.format(self.start_date, self.end_date, total_dates)

    def ffill(self, inplace: bool = False, limit: int = None) -> Union[TimeSeries, None]:
        """Forward fill missing dates in the time series

        Parameters
        ----------
        inplace : bool
            Modify the time-series data in place and return None.

        limit : int, optional
            Maximum number of periods to forward fill

        Returns
        -------
            Returns a TimeSeries object if inplace is False, otherwise None
        """

        eomonth = True if self.frequency.days >= AllFrequencies.M.days else False
        dates_to_fill = create_date_series(self.start_date, self.end_date, self.frequency.symbol, eomonth)

        new_ts = dict()
        for cur_date in dates_to_fill:
            try:
                cur_val = self.data[cur_date]
            except KeyError:
                pass
            new_ts.update({cur_date: cur_val})

        if inplace:
            self.data = new_ts
            return None

        return self.__class__(new_ts, frequency=self.frequency.symbol)

    def bfill(self, inplace: bool = False, limit: int = None) -> Union[TimeSeries, None]:
        """Backward fill missing dates in the time series

        Parameters
        ----------
        inplace : bool
            Modify the time-series data in place and return None.

        limit : int, optional
            Maximum number of periods to back fill

        Returns
        -------
            Returns a TimeSeries object if inplace is False, otherwise None
        """

        eomonth = True if self.frequency.days >= AllFrequencies.M.days else False
        dates_to_fill = create_date_series(self.start_date, self.end_date, self.frequency.symbol, eomonth)
        dates_to_fill.append(self.end_date)

        bfill_ts = dict()
        for cur_date in reversed(dates_to_fill):
            try:
                cur_val = self.data[cur_date]
            except KeyError:
                pass
            bfill_ts.update({cur_date: cur_val})
        new_ts = {k: bfill_ts[k] for k in reversed(bfill_ts)}
        if inplace:
            self.data = new_ts
            return None

        return self.__class__(new_ts, frequency=self.frequency.symbol)

    def calculate_returns(
        self,
        as_on: Union[str, datetime.datetime],
        return_actual_date: bool = True,
        as_on_match: str = "closest",
        prior_match: str = "closest",
        closest: str = "previous",
        if_not_found: Literal['fail', 'nan'] = 'fail',
        compounding: bool = True,
        interval_type: Literal['years', 'months', 'days'] = 'years',
        interval_value: int = 1,
        date_format: str = None
    ) -> float:
        """Method to calculate returns for a certain time-period as on a particular date

        Parameters
        ----------
        as_on : datetime.datetime
            The date as on which the return is to be calculated.

        return_actual_date : bool, default True
            If true, the output will contain the actual date based on which the return was calculated.
            Set to False to return the date passed in the as_on argument.

        as_on_match : str, optional
            The mode of matching the as_on_date. Refer closest.

        prior_match : str, optional
            The mode of matching the prior_date. Refer closest.

        closest : str, optional
            The mode of matching the closest date.
            Valid values are 'exact', 'previous', 'next' and next.

        if_not_found : 'fail' | 'nan'
            What to do when required date is not found:
            * fail: Raise a ValueError
            * nan: Return nan as the value

        compounding : bool, optional
            Whether the return should be compounded annually.

        interval_type : 'years', 'months', 'days'
            The type of time period to use for return calculation.

        interval_value : int
            The value of the specified interval type over which returns needs to be calculated.

        date_format: str
            The date format to use for this operation.
            Should be passed as a datetime library compatible string.
            Sets the date format only for this operation. To set it globally, use FincalOptions.date_format

        Returns
        -------
        A tuple containing the date and float value of the returns.

        Raises
        ------
        ValueError
            * If match mode for any of the dates is exact and the exact match is not found
            * If the arguments passsed for closest, as_on_match, and prior_match are invalid

        Example
        --------
        >>> calculate_returns(datetime.date(2020, 1, 1), years=1)
        """

        as_on = _parse_date(as_on, date_format)
        as_on_delta, prior_delta = _preprocess_match_options(as_on_match, prior_match, closest)

        prev_date = as_on - relativedelta(**{interval_type: interval_value})
        current = _find_closest_date(self.data, as_on, as_on_delta, if_not_found)
        previous = _find_closest_date(self.data, prev_date, prior_delta, if_not_found)

        if current[1] == str('nan') or previous[1] == str('nan'):
            return as_on, float('NaN')

        returns = current[1] / previous[1]
        if compounding:
            years = _interval_to_years(interval_type, interval_value)
            returns = returns ** (1 / years)
        return (current[0] if return_actual_date else as_on), returns - 1

    def calculate_rolling_returns(
        self,
        from_date: Union[datetime.date, str],
        to_date: Union[datetime.date, str],
        frequency: str = None,
        as_on_match: str = "closest",
        prior_match: str = "closest",
        closest: str = "previous",
        if_not_found: Literal['fail', 'nan'] = 'fail',
        compounding: bool = True,
        interval_type: Literal['years', 'months', 'days'] = 'years',
        interval_value: int = 1,
        date_format: str = None
    ) -> List[tuple]:
        """Calculates the rolling return"""

        from_date = _parse_date(from_date, date_format)
        to_date = _parse_date(to_date, date_format)

        if frequency is None:
            frequency = self.frequency
        else:
            try:
                frequency = getattr(AllFrequencies, frequency)
            except AttributeError:
                raise ValueError(f"Invalid argument for frequency {frequency}")

        dates = create_date_series(from_date, to_date, frequency.symbol)
        if frequency == AllFrequencies.D:
            dates = [i for i in dates if i in self.data]

        rolling_returns = []
        for i in dates:
            returns = self.calculate_returns(
                as_on=i,
                compounding=compounding,
                interval_type=interval_type,
                interval_value=interval_value,
                as_on_match=as_on_match,
                prior_match=prior_match,
                closest=closest,
                if_not_found=if_not_found
            )
            rolling_returns.append(returns)
        rolling_returns.sort()
        return self.__class__(rolling_returns, self.frequency.symbol)


if __name__ == "__main__":
    date_series = [
        datetime.datetime(2020, 1, 11),
        datetime.datetime(2020, 1, 12),
        datetime.datetime(2020, 1, 13),
        datetime.datetime(2020, 1, 14),
        datetime.datetime(2020, 1, 17),
        datetime.datetime(2020, 1, 18),
        datetime.datetime(2020, 1, 19),
        datetime.datetime(2020, 1, 20),
        datetime.datetime(2020, 1, 22),
    ]
