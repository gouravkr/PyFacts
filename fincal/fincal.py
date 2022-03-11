from __future__ import annotations

import datetime
import math
import statistics
from typing import Iterable, List, Literal, Mapping, Union

from dateutil.relativedelta import relativedelta

from .core import AllFrequencies, Series, TimeSeriesCore, date_parser
from .utils import (
    FincalOptions,
    _find_closest_date,
    _interval_to_years,
    _preprocess_match_options,
)


@date_parser(0, 1)
def create_date_series(
    start_date: Union[str, datetime.datetime],
    end_date: Union[str, datetime.datetime],
    frequency: Literal["D", "W", "M", "Q", "H", "Y"],
    eomonth: bool = False,
    skip_weekends: bool = False,
) -> List[datetime.datetime]:
    """Create a date series with a specified frequency

    Parameters
    ----------
    start_date : str | datetime.datetime
        Date series will always start at this date

    end_date : str | datetime.datetime
        The date till which the series should extend
        Depending on the other parameters, this date may or may not be present
        in the final date series

    frequency : D | W | M | Q | H | Y
        Frequency of the date series.
        The gap between each successive date will be equivalent to this frequency

    eomonth : bool, optional
        Speacifies if the dates in the series should be end of month dates.
        Can only be used if the frequency is Monthly or lower.

    Returns
    -------
    List[datetime.datetime]
        Returns the series as a list of datetime objects

    Raises
    ------
    ValueError
        If eomonth is True and frequency is higher than monthly
    """

    frequency = getattr(AllFrequencies, frequency)
    if eomonth and frequency.days < AllFrequencies.M.days:
        raise ValueError(f"eomonth cannot be set to True if frequency is higher than {AllFrequencies.M.name}")

    datediff = (end_date - start_date).days / frequency.days + 1
    dates = []

    for i in range(0, int(datediff)):
        diff = {frequency.freq_type: frequency.value * i}
        date = start_date + relativedelta(**diff)

        if eomonth:
            next_month = 1 if date.month == 12 else date.month + 1
            date = date.replace(day=1).replace(month=next_month) - relativedelta(days=1)

        if date <= end_date:
            if frequency.days > 1 or not skip_weekends:
                dates.append(date)
            elif date.weekday() < 5:
                dates.append(date)

    return Series(dates, data_type="date")


class TimeSeries(TimeSeriesCore):
    """1-Dimensional Time Series object

    Parameters
    ----------
    data : List[Iterable] | Mapping
        Time Series data in the form of list of tuples.
        The first element of each tuple should be a date and second element should be a value.
        The following types of objects can be passed to create a TimeSeries object:
        * List of tuples containing date & value
        * List of lists containing date & value
        * List of dictionaries containing key: value pair of date and value
        * List of dictionaries with 2 keys, first representing date & second representing value
        * Dictionary of key: value pairs

    date_format : str, optional, default "%Y-%m-%d"
        Specify the format of the date
        Required only if the first argument of tuples is a string. Otherwise ignored.

    frequency : str, optional, default "infer"
        The frequency of the time series. Default is infer.
        The class will try to infer the frequency automatically and adjust to the closest member.
        Note that inferring frequencies can fail if the data is too irregular.
        Valid values are {D, W, M, Q, H, Y}
    """

    def __init__(
        self,
        data: Union[List[Iterable], Mapping],
        frequency: Literal["D", "W", "M", "Q", "H", "Y"],
        date_format: str = "%Y-%m-%d",
    ):
        """Instantiate a TimeSeriesCore object"""

        super().__init__(data, frequency, date_format)

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

    @date_parser(1)
    def calculate_returns(
        self,
        as_on: Union[str, datetime.datetime],
        return_actual_date: bool = True,
        as_on_match: str = "closest",
        prior_match: str = "closest",
        closest: Literal["previous", "next", "exact"] = "previous",
        closest_max_days: int = -1,
        if_not_found: Literal["fail", "nan"] = "fail",
        annual_compounded_returns: bool = True,
        interval_type: Literal["years", "months", "days"] = "years",
        interval_value: int = 1,
        date_format: str = None,
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

        closest_max_days: int, default -1
            The maximum acceptable gap between the provided date arguments and actual date.
            Pass -1 for no limit.
            Note: There's a hard max limit of 1000 days due to Python's limits on recursion.
                  This can be overridden by importing the sys module.

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
        (datetime.datetime(2020, 1, 1, 0, 0), .0567)
        """

        as_on_delta, prior_delta = _preprocess_match_options(as_on_match, prior_match, closest)

        prev_date = as_on - relativedelta(**{interval_type: interval_value})
        current = _find_closest_date(self.data, as_on, closest_max_days, as_on_delta, if_not_found)
        if current[1] != str("nan"):
            previous = _find_closest_date(self.data, prev_date, closest_max_days, prior_delta, if_not_found)

        if current[1] == str("nan") or previous[1] == str("nan"):
            return as_on, float("NaN")

        returns = current[1] / previous[1]
        if annual_compounded_returns:
            years = _interval_to_years(interval_type, interval_value)
            returns = returns ** (1 / years)
        return (current[0] if return_actual_date else as_on), returns - 1

    @date_parser(1, 2)
    def calculate_rolling_returns(
        self,
        from_date: Union[datetime.date, str],
        to_date: Union[datetime.date, str],
        frequency: Literal["D", "W", "M", "Q", "H", "Y"] = None,
        as_on_match: str = "closest",
        prior_match: str = "closest",
        closest: Literal["previous", "next", "exact"] = "previous",
        if_not_found: Literal["fail", "nan"] = "fail",
        annual_compounded_returns: bool = True,
        interval_type: Literal["years", "months", "days"] = "years",
        interval_value: int = 1,
        date_format: str = None,
    ) -> TimeSeries:
        """Calculate the returns on a rolling basis.
            This is a wrapper function around the calculate_returns function.

        Parameters
        ----------
        from_date : datetime.date | str
            Start date for the return calculation.

        to_date : datetime.date | str
            End date for the returns calculation.

        frequency : str, optional
            Frequency at which the returns should be calcualated.
            Valid values are {D, W, M, Q, H, Y}

        as_on_match : str, optional
            The match mode to be used for the as on date.
            If not specified, the value for the closes parameter will be used.

        prior_match : str, optional
            The match mode to be used for the prior date, i.e., the date against which the return will be calculated.
            If not specified, the value for the closes parameter will be used.

        closest : previous | next | exact
            The default match mode for dates.
            * Previous: look for the immediate previous available date
            * Next: look for the immediate next available date
            * Exact: Only look for the exact date passed in the input

        if_not_found : fail | nan
            Specifies what should be done if the date is not found.
            * fail: raise a DateNotFoundError.
            * nan: return nan as the value.
                Note, this will return float('NaN') and not 'nan' as string.

            Note, this function will always raise an error if it is not possible to find a matching date.`
            For instance, if the input date is before the starting of the first date of the time series,
            but match mode is set to previous. A DateOutOfRangeError will be raised in such cases.

        compounding : bool, optional
            Should the returns be compounded annually.

        interval_type : years | month | days
            The interval for the return calculation.

        interval_value : int, optional
            The value of the interval for return calculation.

        date_format : str, optional
            A datetime library compatible format string.
            If not specified, will use the setting in FincalOptions.date_format.

        Returns
        -------
            Returs the rolling returns as a TimeSeries object.

        Raises
        ------
            ValueError
            - If an invalid argument is passed for frequency parameter.

        See also
        --------
            TimeSeries.calculate_returns
        """

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
                annual_compounded_returns=annual_compounded_returns,
                interval_type=interval_type,
                interval_value=interval_value,
                as_on_match=as_on_match,
                prior_match=prior_match,
                closest=closest,
                if_not_found=if_not_found,
            )
            rolling_returns.append(returns)
        rolling_returns.sort()
        return self.__class__(rolling_returns, self.frequency.symbol)

    @date_parser(1, 2)
    def volatility(
        self,
        from_date: Union[datetime.date, str] = None,
        to_date: Union[datetime.date, str] = None,
        frequency: Literal["D", "W", "M", "Q", "H", "Y"] = None,
        as_on_match: str = "closest",
        prior_match: str = "closest",
        closest: Literal["previous", "next", "exact"] = "previous",
        if_not_found: Literal["fail", "nan"] = "fail",
        annual_compounded_returns: bool = None,
        interval_type: Literal["years", "months", "days"] = "days",
        interval_value: int = 1,
        date_format: str = None,
        annualize_volatility: bool = True,
        traded_days: int = None,
    ):
        """Calculates the volatility of the time series.add()

        The volatility is calculated as the standard deviaion of periodic returns.
        The periodicity of returns is based on the periodicity of underlying data.
        """

        if frequency is None:
            frequency = self.frequency
        else:
            try:
                frequency = getattr(AllFrequencies, frequency)
            except AttributeError:
                raise ValueError(f"Invalid argument for frequency {frequency}")

        if from_date is None:
            from_date = self.start_date + relativedelta(**{interval_type: interval_value})
        if to_date is None:
            to_date = self.end_date

        if annual_compounded_returns is None:
            annual_compounded_returns = False if frequency.days <= 366 else True

        rolling_returns = self.calculate_rolling_returns(
            from_date=from_date,
            to_date=to_date,
            frequency=frequency.symbol,
            as_on_match=as_on_match,
            prior_match=prior_match,
            closest=closest,
            if_not_found=if_not_found,
            annual_compounded_returns=annual_compounded_returns,
            interval_type=interval_type,
            interval_value=interval_value,
        )
        sd = statistics.stdev(rolling_returns.values)
        if annualize_volatility:
            if traded_days is None:
                traded_days = FincalOptions.traded_days

            if interval_type == "months":
                sd *= math.sqrt(12)
            elif interval_type == "days":
                sd *= math.sqrt(traded_days)

        return sd


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
