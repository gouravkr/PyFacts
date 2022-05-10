from __future__ import annotations

import csv
import datetime
import math
import pathlib
import statistics
from typing import Iterable, List, Literal, Mapping, Tuple, TypedDict

from dateutil.relativedelta import relativedelta

from .core import AllFrequencies, Frequency, Series, TimeSeriesCore, date_parser
from .utils import (
    FincalOptions,
    _find_closest_date,
    _interval_to_years,
    _preprocess_match_options,
)


class MaxDrawdown(TypedDict):
    start_date: datetime.datetime
    end_date: datetime.datetime
    drawdown: float


@date_parser(0, 1)
def create_date_series(
    start_date: str | datetime.datetime,
    end_date: str | datetime.datetime,
    frequency: Literal["D", "W", "M", "Q", "H", "Y"],
    eomonth: bool = False,
    skip_weekends: bool = False,
    ensure_coverage: bool = False,
) -> Series:
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

    skip_weekends: Boolean, default False
        If set to True, dates falling on weekends will not be added to the series.
        Used only when frequency is daily, weekends will necessarily be included for other frequencies.

    ensure_coverage: Boolean, default False
        If set to true, it will ensure the last date is greater than the end date.

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

    if ensure_coverage:
        if frequency.days == 1 and skip_weekends and end_date.weekday() > 4:
            extend_by_days = 7 - end_date.weekday()
            end_date += relativedelta(days=extend_by_days)

        # To-do: Add code to ensure coverage for other frequencies as well

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

    return Series(dates, dtype="date")


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
        data: List[Iterable] | Mapping,
        frequency: Literal["D", "W", "M", "Q", "H", "Y"],
        date_format: str = "%Y-%m-%d",
    ):
        """Instantiate a TimeSeriesCore object"""

        super().__init__(data, frequency, date_format)

    def info(self) -> str:
        """Summary info about the TimeSeries object"""

        total_dates: int = len(self.data.keys())
        res_string: str = "First date: {}\nLast date: {}\nNumber of rows: {}"
        return res_string.format(self.start_date, self.end_date, total_dates)

    def ffill(
        self, inplace: bool = False, limit: int = 1000, skip_weekends: bool = False, eomonth: bool = False
    ) -> TimeSeries | None:
        """Forward fill missing dates in the time series

        Parameters
        ----------
        inplace : bool
            Modify the time-series data in place and return None.

        limit : int, optional
            Maximum number of periods to forward fill

        skip_weekends: bool, optional, default false
            Skip weekends while forward filling daily data

        Returns
        -------
            Returns a TimeSeries object if inplace is False, otherwise None
        """

        dates_to_fill = create_date_series(
            self.start_date, self.end_date, self.frequency.symbol, eomonth, skip_weekends=skip_weekends
        )

        new_ts = dict()
        counter = 0
        for cur_date in dates_to_fill:
            try:
                new_val = self[cur_date]
                cur_val = new_val
                counter = 0
            except KeyError:
                if counter >= limit:
                    continue
                counter += 1
            new_ts.update({cur_date: cur_val[1]})

        if inplace:
            self.data = new_ts
            return None

        return self.__class__(new_ts, frequency=self.frequency.symbol)

    def bfill(
        self, inplace: bool = False, limit: int = 1000, skip_weekends: bool = False, eomonth: bool = False
    ) -> TimeSeries | None:
        """Backward fill missing dates in the time series

        Parameters
        ----------
        inplace : bool
            Modify the time-series data in place and return None.

        limit : int, optional
            Maximum number of periods to back fill

        skip_weekends: bool, optional, default false
            Skip weekends while forward filling daily data

        Returns
        -------
            Returns a TimeSeries object if inplace is False, otherwise None
        """

        dates_to_fill = create_date_series(
            self.start_date, self.end_date, self.frequency.symbol, eomonth, skip_weekends=skip_weekends
        )
        dates_to_fill.append(self.end_date)

        bfill_ts = dict()
        counter = 0
        for cur_date in reversed(dates_to_fill):
            try:
                new_val = self[cur_date]
                cur_val = new_val
                counter = 0
            except KeyError:
                if counter >= limit:
                    continue
                counter += 1
            bfill_ts.update({cur_date: cur_val[1]})
        # new_ts = {k: bfill_ts[k] for k in reversed(bfill_ts)}
        new_ts = dict(list(reversed(bfill_ts.items())))
        if inplace:
            self.data = new_ts
            return None

        return self.__class__(new_ts, frequency=self.frequency.symbol)

    @date_parser(1)
    def calculate_returns(
        self,
        as_on: str | datetime.datetime,
        return_actual_date: bool = True,
        as_on_match: str = "closest",
        prior_match: str = "closest",
        closest: Literal["previous", "next", "exact"] = "previous",
        closest_max_days: int = -1,
        if_not_found: Literal["fail", "nan"] = "fail",
        annual_compounded_returns: bool = True,
        return_period_unit: Literal["years", "months", "days"] = "years",
        return_period_value: int = 1,
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

        return_period_unit : 'years', 'months', 'days'
            The type of time period to use for return calculation.

        return_period_value : int
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

        prev_date = as_on - relativedelta(**{return_period_unit: return_period_value})
        current = _find_closest_date(self.data, as_on, closest_max_days, as_on_delta, if_not_found)
        if current[1] != str("nan"):
            previous = _find_closest_date(self.data, prev_date, closest_max_days, prior_delta, if_not_found)

        if current[1] == str("nan") or previous[1] == str("nan"):
            return as_on, float("NaN")

        returns = current[1] / previous[1]
        if annual_compounded_returns:
            years = _interval_to_years(return_period_unit, return_period_value)
            returns = returns ** (1 / years)
        return (current[0] if return_actual_date else as_on), returns - 1

    @date_parser(1, 2)
    def calculate_rolling_returns(
        self,
        from_date: datetime.date | str,
        to_date: datetime.date | str,
        frequency: Literal["D", "W", "M", "Q", "H", "Y"] = None,
        as_on_match: str = "closest",
        prior_match: str = "closest",
        closest: Literal["previous", "next", "exact"] = "previous",
        if_not_found: Literal["fail", "nan"] = "fail",
        annual_compounded_returns: bool = True,
        return_period_unit: Literal["years", "months", "days"] = "years",
        return_period_value: int = 1,
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

        return_period_unit : years | month | days
            The interval for the return calculation.

        return_period_value : int, optional
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
                return_period_unit=return_period_unit,
                return_period_value=return_period_value,
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
        from_date: datetime.date | str = None,
        to_date: datetime.date | str = None,
        annualize_volatility: bool = True,
        traded_days: int = None,
        frequency: Literal["D", "W", "M", "Q", "H", "Y"] = None,
        return_period_unit: Literal["years", "months", "days"] = "days",
        return_period_value: int = 1,
        as_on_match: str = "closest",
        prior_match: str = "closest",
        closest: Literal["previous", "next", "exact"] = "previous",
        if_not_found: Literal["fail", "nan"] = "fail",
        annual_compounded_returns: bool = None,
        date_format: str = None,
    ) -> float:
        """Calculates the volatility of the time series.add()

        The volatility is calculated as the standard deviaion of periodic returns.
        The periodicity of returns is based on the periodicity of underlying data.

        Parameters:
        ----------
        from_date: datetime.datetime | str, optional
            Starting date for the volatility calculation.
            Default is the first date on which volatility can be calculated based on the interval type.

        to_date: datetime.datetime | str, optional
            Ending date for the volatility calculation.
            Default is the last date in the TimeSeries.

        annualize_volatility: bool, default True
            Whether the volatility number should be annualized.
            Multiplies the standard deviation with the square root of the number of periods in a year

        traded_days: bool, optional
            Number of traded days per year to be considered for annualizing volatility.
            Only used when annualizing volatility for a time series with daily frequency.
            If not provided, will use the value in FincalOptions.traded_days.

        Remaining options are passed on to calculate_rolling_returns function.

        Returns:
        -------
            Returns the volatility number as float

        Raises:
        -------
            ValueError: If frequency string is outside valid values

        Also see:
        ---------
            TimeSeries.calculate_rolling_returns()
        """

        if frequency is None:
            frequency = self.frequency
        else:
            try:
                frequency = getattr(AllFrequencies, frequency)
            except AttributeError:
                raise ValueError(f"Invalid argument for frequency {frequency}")

        if from_date is None:
            from_date = self.start_date + relativedelta(**{return_period_unit: return_period_value})
        if to_date is None:
            to_date = self.end_date
        years = _interval_to_years(return_period_unit, return_period_value)
        if annual_compounded_returns is None:
            if years > 1:
                annual_compounded_returns = True
            else:
                annual_compounded_returns = False

        rolling_returns = self.calculate_rolling_returns(
            from_date=from_date,
            to_date=to_date,
            frequency=frequency.symbol,
            as_on_match=as_on_match,
            prior_match=prior_match,
            closest=closest,
            if_not_found=if_not_found,
            annual_compounded_returns=annual_compounded_returns,
            return_period_unit=return_period_unit,
            return_period_value=return_period_value,
        )
        sd = statistics.stdev(rolling_returns.values)
        if annualize_volatility:
            if traded_days is None:
                traded_days = FincalOptions.traded_days

            if return_period_unit == "months":
                sd *= math.sqrt(12 / return_period_value)
            elif return_period_unit == "days":
                sd *= math.sqrt(traded_days / return_period_value)

        return sd

    def average_rolling_return(self, **kwargs) -> float:
        """Calculates the average rolling return for a given period

        Parameters
        ----------
        kwargs: parameters to be passed to the calculate_rolling_returns() function

        Returns
        -------
        float
            returns the average rolling return for a given period

        Also see:
        ---------
        TimeSeries.calculate_rolling_returns()
        """
        kwargs["return_period_unit"] = kwargs.get("return_period_unit", self.frequency.freq_type)
        kwargs["return_period_value"] = kwargs.get("return_period_value", 1)

        years = _interval_to_years(kwargs["return_period_unit"], kwargs["return_period_value"])
        if kwargs.get("annual_compounded_returns", True):
            if years >= 1:
                kwargs["annual_compounded_returns"] = True
                annualise_returns = False
            else:
                kwargs["annual_compounded_returns"] = False
                annualise_returns = True
        elif not kwargs["annual_compounded_returns"]:
            annualise_returns = False

        if kwargs.get("from_date") is None:
            kwargs["from_date"] = self.start_date + relativedelta(
                **{kwargs["return_period_unit"]: kwargs["return_period_value"]}
            )
        kwargs["to_date"] = kwargs.get("to_date", self.end_date)

        rr = self.calculate_rolling_returns(**kwargs)
        mean_rr = statistics.mean(rr.values)
        if annualise_returns:
            mean_rr = (1 + mean_rr) ** (1 / years) - 1

        return mean_rr

    def max_drawdown(self) -> MaxDrawdown:
        """Calculates the maximum fall the stock has taken between any two points.

        Returns
        -------
        MaxDrawdown
            Returns the start_date, end_date, and the drawdown value in decimal.
        """

        drawdowns: dict = dict()

        prev_val: float = 0
        prev_date: datetime.datetime = list(self.data)[0]

        for dt, val in self.data.items():
            if val > prev_val:
                drawdowns[dt] = (dt, val, 0)
                prev_date, prev_val = dt, val
            else:
                drawdowns[dt] = (prev_date, prev_val, val / prev_val - 1)

        max_drawdown = min(drawdowns.items(), key=lambda x: x[1][2])
        max_drawdown: MaxDrawdown = dict(
            start_date=max_drawdown[1][0], end_date=max_drawdown[0], drawdown=max_drawdown[1][2]
        )

        return max_drawdown

    def expand(
        self,
        to_frequency: Literal["D", "W", "M", "Q", "H"],
        method: Literal["ffill", "bfill"],
        skip_weekends: bool = False,
        eomonth: bool = False,
    ) -> TimeSeries:
        """Expand a time series to a higher frequency.

        Parameters
        ----------
        to_frequency : "D", "W", "M", "Q", "H"
            Frequency to which the TimeSeries will be expanded.
            Must be higher than the current frequency of the TimeSeries.

        method : ffill | bfill
            Method to be used to fill missing values.

        skip_weekends : bool, optional
            Whether weekends should be skipped while expanding to daily.
            Will be used only if to_frequency is D

        eomonth: bool, optional
            Whether dates should be end of month dates when frequency is monthly or lower.
            Will be used only if to_frequency is M, Q, or H

        Returns
        -------
        TimeSeries
            Returns an object of TimeSeries class

        Raises
        ------
        ValueError
            * If Frequency cannot be recognised
            * If to_frequency is same or lower than the current frequency
        """
        try:
            to_frequency: Frequency = getattr(AllFrequencies, to_frequency)
        except AttributeError:
            raise ValueError(f"Invalid argument for to_frequency {to_frequency}")

        if to_frequency.days >= self.frequency.days:
            raise ValueError("TimeSeries can be only expanded to a higher frequency")

        new_dates = create_date_series(
            self.start_date,
            self.end_date,
            frequency=to_frequency.symbol,
            skip_weekends=skip_weekends,
            eomonth=eomonth,
            ensure_coverage=True,
        )

        closest: str = "previous" if method == "ffill" else "next"
        new_ts: dict = {dt: self.get(dt, closest=closest)[1] for dt in new_dates}
        output_ts: TimeSeries = TimeSeries(new_ts, frequency=to_frequency.symbol)

        return output_ts

    def shrink(
        self,
        to_frequency: Literal["W", "M", "Q", "H", "Y"],
        method: Literal["ffill", "bfill"],
        skip_weekends: bool = False,
        eomonth: bool = False,
    ) -> TimeSeries:
        """Shrink a time series to a lower frequency.

        Parameters
        ----------
        to_frequency : "W", "M", "Q", "H", "Y"
            Frequency to which the TimeSeries will be shrunk.
            Must be lower than the current frequency of the TimeSeries.

        method : ffill | bfill
            Method to be used to fill missing values.

        skip_weekends : bool, optional
            Whether weekends should be skipped while shrinking to daily.
            Will be used only if to_frequency is D

        eomonth: bool, optional
            Whether dates should be end of month dates when frequency is monthly or lower.
            Will be used only if to_frequency is M, Q, H, or Y

        Returns
        -------
        TimeSeries
            Returns an object of TimeSeries class

        Raises
        ------
        ValueError
            * If Frequency cannot be recognised
            * If to_frequency is same or higher than the current frequency
        """
        try:
            to_frequency: Frequency = getattr(AllFrequencies, to_frequency)
        except AttributeError:
            raise ValueError(f"Invalid argument for to_frequency {to_frequency}")

        if to_frequency.days <= self.frequency.days:
            raise ValueError("TimeSeries can be only shrunk to a lower frequency")

        new_dates = create_date_series(
            self.start_date,
            self.end_date,
            frequency=to_frequency.symbol,
            skip_weekends=skip_weekends,
            eomonth=eomonth,
            ensure_coverage=True,
        )

        closest: str = "previous" if method == "ffill" else "next"
        new_ts: dict = {dt: self.get(dt, closest=closest)[1] for dt in new_dates}
        output_ts: TimeSeries = TimeSeries(new_ts, frequency=to_frequency.symbol)

        return output_ts

    def sync(self, other: TimeSeries, fill_method: Literal["ffill", "bfill"] = "ffill") -> TimeSeries:
        """Synchronize two TimeSeries objects

        This will ensure that both time series have the same frequency and same set of dates.
        The frequency will be set to the higher of the two objects.
        Dates will be taken from the class on which the method is called.
        Values will be taken from the other class.

        Parameters:
        -----------
        other: TimeSeries
            Another object of TimeSeries class whose dates need to be syncronized

        fill_method: ffill | bfill, default ffill
            Method to use to fill missing values in time series when syncronizing

        Returns:
        --------
            Returns another object of TimeSeries class

        Raises:
        --------
            Raises TypeError if the other object is not of TimeSeries class
        """

        if not isinstance(other, TimeSeries):
            raise TypeError("Only objects of type TimeSeries can be passed for sync")

        if self.frequency.days < other.frequency.days:
            other = other.expand(to_frequency=self.frequency.symbol, method=fill_method)
        if self.frequency.days > other.frequency.days:
            other = other.shrink(to_frequency=other.frequency.symbol, method=fill_method)

        new_other: dict = {}
        closest = "previous" if fill_method == "ffill" else "next"
        for dt in self.dates:
            if dt in other:
                new_other[dt] = other[dt][1]
            else:
                new_other[dt] = other.get(dt, closest=closest)[1]

        return self.__class__(new_other, frequency=other.frequency.symbol)

    def mean(self) -> float:
        """Calculates the mean value of the time series data"""

        return statistics.mean(self.values)


def _preprocess_csv(file_path: str | pathlib.Path, delimiter: str = ",", encoding: str = "utf-8") -> List[list]:
    """Preprocess csv data"""

    if isinstance(file_path, str):
        file_path = pathlib.Path(file_path)

    if not file_path.exists():
        raise ValueError("File not found. Check the file path")

    with open(file_path, "r", encoding=encoding) as file:
        reader: csv.reader = csv.reader(file, delimiter=delimiter)
        csv_data: list = list(reader)

    csv_data = [i for i in csv_data if i]  # remove blank rows
    if not csv_data:
        raise ValueError("File is empty")

    return csv_data


def read_csv(
    csv_file_path: str | pathlib.Path,
    frequency: Literal["D", "W", "M", "Q", "Y"],
    date_format: str = None,
    col_names: Tuple[str, str] = None,
    col_index: Tuple[int, int] = (0, 1),
    has_header: bool = True,
    skip_rows: int = 0,
    nrows: int = -1,
    delimiter: str = ",",
    encoding: str = "utf-8",
) -> TimeSeries:
    """Reads Time Series data directly from a CSV file"""

    data = _preprocess_csv(csv_file_path, delimiter, encoding)

    read_start_row = skip_rows
    read_end_row = skip_rows + nrows if nrows >= 0 else None

    if has_header:
        header = data[read_start_row]
        print(header)
        # fmt: off
        # Black and pylance disagree on the foratting of the following line, hence formatting is disabled
        data = data[(read_start_row + 1):read_end_row]
        # fmt: on

    if col_names is not None:
        date_col = header.index(col_names[0])
        value_col = header.index(col_names[1])
    else:
        date_col = col_index[0]
        value_col = col_index[1]

    ts_data = [(i[date_col], i[value_col]) for i in data if i]

    return TimeSeries(ts_data, frequency=frequency, date_format=date_format)


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
