from __future__ import annotations

import datetime
import statistics
from dataclasses import dataclass
from typing import List, Literal, Mapping, Sequence, Tuple

from dateutil.relativedelta import relativedelta

from .exceptions import DateNotFoundError, DateOutOfRangeError


@dataclass
class PyfactsOptions:
    date_format: str = "%Y-%m-%d"
    closest: str = "previous"  # next
    traded_days: int = 365
    get_closest: str = "exact"


def _parse_date(date: str, date_format: str = None) -> datetime.datetime:
    """Parses date and handles errors

    Parameters:
    -----------
    date: str | datetime.date
        The date to be parsed.
        If the date passed is already a datetime object, it will return it unprocessed.

    date_format: str, default None
        The format of the date string in datetime.strftime friendly format.
        If format is None, format in FincalOptions.date_format will be used.

    Returns:
    --------
        Returns a datetime.datetime object.

    Raises:
    -------
        TypeError: If the is not a date-like string
        ValueError: If the date could not be parsed with the given format
    """

    if isinstance(date, (datetime.datetime, datetime.date)):
        return datetime.datetime.fromordinal(date.toordinal())

    if date_format is None:
        date_format = PyfactsOptions.date_format

    try:
        date = datetime.datetime.strptime(date, date_format)
    except TypeError:
        raise ValueError("Date does not seem to be valid date-like string")
    except ValueError:
        raise ValueError("Date could not be parsed. Have you set the correct date format in FincalOptions.date_format?")
    return date


def _preprocess_timeseries(
    data: Sequence[Tuple[str | datetime.datetime, float]]
    | Sequence[Mapping[str | datetime.datetime, float]]
    | Mapping[str | datetime.datetime, float],
    date_format: str,
) -> List[Tuple[datetime.datetime, float]]:
    """Converts any type of list to the TimeSeries friendly format.
        This function is internally called by the __init__ function of the TimeSeriesCore class

        The TimeSeries class can internally process a list of Tuples.
        However, users have the option of passing a variety of types.
        This function preprocesses the data and converts it into the relevant format.

        If the data is a dictionary, it will be converted using .items() iteration.
        If the data is not a dictionary or a list, it will raise an error.
        If the data is of list type:
            * If the first item is also of list type, it will be parsed as a list of lists
            * If the first item is a dictionary with one key, then key will be parsed as date
            * If the first item is a dictionary with two keys, then first key will be date and second will be value
            * If the first element is of another type, it will raise an error

        The final return value is sorted by date

    Parameters:
    -----------
    Data:
        The data for the time series. Can be a dictionary, a list of tuples, or a list of dictionaries.

    date_format: str
        The format of the date in strftime friendly format.

    Returns:
    -----------
        Returns a list of Tuples where the first element of each tuple is of datetime.datetime class
        and the second element is of float class

    Raises:
    --------
    TypeError: If the data is not in a format which can be parsed.
    """

    if isinstance(data, Mapping):
        current_data: List[tuple] = [(k, v) for k, v in data.items()]
        return _preprocess_timeseries(current_data, date_format)

    # If data is not a dictionary or list, it cannot be parsed
    if not isinstance(data, Sequence):
        raise TypeError("Could not parse the data")

    if isinstance(data[0], Sequence):
        return sorted([(_parse_date(i, date_format), float(j)) for i, j in data])

    # If first element is not a dictionary or tuple, it cannot be parsed
    if not isinstance(data[0], Mapping):
        raise TypeError("Could not parse the data")

    if len(data[0]) == 1:
        current_data: List[tuple] = [tuple(*i.items()) for i in data]
    elif len(data[0]) == 2:
        current_data: List[tuple] = [tuple(i.values()) for i in data]
    else:
        raise TypeError("Could not parse the data")
    return _preprocess_timeseries(current_data, date_format)


def _preprocess_match_options(as_on_match: str, prior_match: str, closest: str) -> Tuple[datetime.timedelta]:
    """Checks the arguments and returns appropriate timedelta objects"""

    deltas = {"exact": 0, "previous": -1, "next": 1}
    if closest not in deltas.keys():
        raise ValueError(f"Invalid argument for closest: {closest}")

    as_on_match: str = closest if as_on_match == "closest" else as_on_match
    prior_match: str = closest if prior_match == "closest" else prior_match

    if as_on_match in deltas.keys():
        as_on_delta: datetime.timedelta = datetime.timedelta(days=deltas[as_on_match])
    else:
        raise ValueError(f"Invalid as_on_match argument: {as_on_match}")

    if prior_match in deltas.keys():
        prior_delta: datetime.timedelta = datetime.timedelta(days=deltas[prior_match])
    else:
        raise ValueError(f"Invalid prior_match argument: {prior_match}")

    return as_on_delta, prior_delta


def _find_closest_date(
    data: Mapping[datetime.datetime, float],
    date: datetime.datetime,
    limit_days: int,
    delta: datetime.timedelta,
    if_not_found: Literal["fail", "nan"],
):
    """Helper function to find data for the closest available date"""

    if delta.days < 0 and date < min(data):
        raise DateOutOfRangeError(date, "min")
    if delta.days > 0 and date > max(data):
        raise DateOutOfRangeError(date, "max")

    row: tuple = data.get(date, None)
    if row is not None:
        return date, row

    if delta and limit_days != 0:
        return _find_closest_date(data, date + delta, limit_days - 1, delta, if_not_found)

    if if_not_found == "fail":
        raise DateNotFoundError("Data not found for date", date)
    if if_not_found == "nan":
        return date, float("NaN")

    raise ValueError(f"Invalid argument for if_not_found: {if_not_found}")


def _interval_to_years(interval_type: Literal["years", "months", "day"], interval_value: int) -> float:
    """Converts any time period to years for use with compounding functions"""

    year_conversion_factor: dict = {"years": 1, "months": 12, "days": 365}
    years: float = interval_value / year_conversion_factor[interval_type]
    return years


def _is_eomonth(dates: Sequence[datetime.datetime], threshold: float = 0.7):
    """Checks if a series is should be treated as end of month date series or not.

    If eomonth dates exceed threshold percentage, it will be treated as eomonth series.
    This can be used for any frequency, but will work only for monthly and lower frequencies.
    """
    eomonth_dates = [date.month != (date + relativedelta(days=1)).month for date in dates]
    eomonth_proportion = sum(eomonth_dates) / len(dates)
    return eomonth_proportion > threshold


def covariance(series1: list, series2: list) -> float:
    """Returns the covariance of two series

        This is a compatibility function for Python versions prior to 3.10.
        It will be replaced with statistics.covariance when support is dropped for versions <3.10.

    Parameters
    ----------
    series1 : List
        A list of numbers
    series2 : list
        A list of numbers

    Returns
    -------
    float
        Returns the covariance as a float value
    """

    n = len(series1)
    if len(series2) != n:
        raise ValueError("Lenght of both series must be same for covariance calcualtion.")
    if n < 2:
        raise ValueError("At least two data poitns are required for covariance calculation.")

    mean1 = statistics.mean(series1)
    mean2 = statistics.mean(series2)

    xy = sum([(x - mean1) * (y - mean2) for x, y in zip(series1, series2)])

    return xy / n
