from __future__ import annotations

import datetime
from typing import List, Union

from dateutil.relativedelta import relativedelta

from .core import AllFrequencies, TimeSeriesCore, _preprocess_match_options


def create_date_series(
    start_date: datetime.datetime, end_date: datetime.datetime, frequency: str, eomonth: bool = False
) -> List[datetime.datetime]:
    """Creates a date series using a frequency"""

    frequency = getattr(AllFrequencies, frequency)
    if eomonth and frequency.days < AllFrequencies.M.days:
        raise ValueError(f"eomonth cannot be set to True if frequency is higher than {AllFrequencies.M.name}")

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

        total_dates = len(self.time_series.keys())
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
                cur_val = self.time_series[cur_date]
            except KeyError:
                pass
            new_ts.update({cur_date: cur_val})

        if inplace:
            self.time_series = new_ts
            return None

        return new_ts

    def bfill(self, inplace=False):
        num_days = (self.end_date - self.start_date).days + 1

        new_ts = dict()
        for i in range(num_days):
            cur_date = self.end_date - datetime.timedelta(days=i)
            try:
                cur_val = self.time_series[cur_date]
            except KeyError:
                pass
            new_ts.update({cur_date: cur_val})

        if inplace:
            self.time_series = new_ts
            return None

        return dict(reversed(new_ts.items()))

    def calculate_returns(
        self,
        as_on: datetime.datetime,
        as_on_match: str = "closest",
        prior_match: str = "closest",
        closest: str = "previous",
        compounding: bool = True,
        years: int = 1,
    ) -> float:
        """Method to calculate returns for a certain time-period as on a particular date

        Parameters
        ----------
        as_on : datetime.datetime
            The date as on which the return is to be calculated.

        as_on_match : str, optional
            The mode of matching the as_on_date. Refer closest.

        prior_match : str, optional
            The mode of matching the prior_date. Refer closest.

        closest : str, optional
            The mode of matching the closest date.
            Valid values are 'exact', 'previous', 'next' and next.

        compounding : bool, optional
            Whether the return should be compounded annually.

        years : int, optional
            number of years for which the returns should be calculated

        Returns
        -------
        The float value of the returns.

        Raises
        ------
        ValueError
            * If match mode for any of the dates is exact and the exact match is not found
            * If the arguments passsed for closest, as_on_match, and prior_match are invalid

        Example
        --------
        >>> calculate_returns(datetime.date(2020, 1, 1), years=1)
        """

        as_on_delta, prior_delta = _preprocess_match_options(as_on_match, prior_match, closest)

        while True:
            current = self.time_series.get(as_on, None)
            if current is not None:
                break
            elif not as_on_delta:
                raise ValueError("As on date not found")
            as_on += as_on_delta

        prev_date = as_on - relativedelta(years=years)
        while True:
            previous = self.time_series.get(prev_date, None)
            if previous is not None:
                break
            elif not prior_delta:
                raise ValueError("Previous date not found")
            prev_date += prior_delta

        returns = current / previous
        if compounding:
            returns = returns ** (1 / years)
        return returns - 1

    def calculate_rolling_returns(
        self,
        from_date: datetime.date,
        to_date: datetime.date,
        frequency: str = "D",
        as_on_match: str = "closest",
        prior_match: str = "closest",
        closest: str = "previous",
        compounding: bool = True,
        years: int = 1,
    ) -> List[tuple]:
        """Calculates the rolling return"""

        try:
            frequency = getattr(AllFrequencies, frequency)
        except AttributeError:
            raise ValueError(f"Invalid argument for frequency {frequency}")

        dates = create_date_series(from_date, to_date, frequency)
        if frequency == AllFrequencies.D:
            dates = [i for i in dates if i in self.time_series]

        rolling_returns = []
        for i in dates:
            returns = self.calculate_returns(
                as_on=i,
                compounding=compounding,
                years=years,
                as_on_match=as_on_match,
                prior_match=prior_match,
                closest=closest,
            )
            rolling_returns.append((i, returns))
        rolling_returns.sort()
        return rolling_returns


if __name__ == "__main__":
    date_series = [
        datetime.datetime(2020, 1, 1),
        datetime.datetime(2020, 1, 2),
        datetime.datetime(2020, 1, 3),
        datetime.datetime(2020, 1, 4),
        datetime.datetime(2020, 1, 7),
        datetime.datetime(2020, 1, 8),
        datetime.datetime(2020, 1, 9),
        datetime.datetime(2020, 1, 10),
        datetime.datetime(2020, 1, 12),
    ]
