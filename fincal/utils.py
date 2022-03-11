import datetime
from dataclasses import dataclass
from typing import Iterable, List, Literal, Mapping, Sequence, Tuple, Union

from .exceptions import DateNotFoundError, DateOutOfRangeError


@dataclass
class FincalOptions:
    date_format: str = "%Y-%m-%d"
    closest: str = "before"  # after
    traded_days: int = 365


def _parse_date(date: str, date_format: str = None):
    """Parses date and handles errors"""
    # print(date, date_format)
    if isinstance(date, (datetime.datetime, datetime.date)):
        return datetime.datetime.fromordinal(date.toordinal())

    if date_format is None:
        date_format = FincalOptions.date_format

    try:
        date = datetime.datetime.strptime(date, date_format)
    except TypeError:
        raise ValueError("Date does not seem to be valid date-like string")
    except ValueError:
        raise ValueError("Date could not be parsed. Have you set the correct date format in FincalOptions.date_format?")
    return date


def _preprocess_timeseries(
    data: Union[
        Sequence[Iterable[Union[str, datetime.datetime, float]]],
        Sequence[Mapping[str, Union[float, datetime.datetime]]],
        Sequence[Mapping[Union[str, datetime.datetime], float]],
        Mapping[Union[str, datetime.datetime], float],
    ],
    date_format: str,
) -> List[Tuple[datetime.datetime, float]]:
    """Converts any type of list to the correct type"""

    if isinstance(data, Mapping):
        current_data = [(k, v) for k, v in data.items()]
        return _preprocess_timeseries(current_data, date_format)

    if not isinstance(data, Sequence):
        raise TypeError("Could not parse the data")

    if isinstance(data[0], Sequence):
        return sorted([(_parse_date(i, date_format), j) for i, j in data])

    if not isinstance(data[0], Mapping):
        raise TypeError("Could not parse the data")

    if len(data[0]) == 1:
        current_data = [tuple(*i.items()) for i in data]
    elif len(data[0]) == 2:
        current_data = [tuple(i.values()) for i in data]
    else:
        raise TypeError("Could not parse the data")
    return _preprocess_timeseries(current_data, date_format)


def _preprocess_match_options(as_on_match: str, prior_match: str, closest: str) -> datetime.timedelta:
    """Checks the arguments and returns appropriate timedelta objects"""

    deltas = {"exact": 0, "previous": -1, "next": 1}
    if closest not in deltas.keys():
        raise ValueError(f"Invalid argument for closest: {closest}")

    as_on_match = closest if as_on_match == "closest" else as_on_match
    prior_match = closest if prior_match == "closest" else prior_match

    if as_on_match in deltas.keys():
        as_on_delta = datetime.timedelta(days=deltas[as_on_match])
    else:
        raise ValueError(f"Invalid as_on_match argument: {as_on_match}")

    if prior_match in deltas.keys():
        prior_delta = datetime.timedelta(days=deltas[prior_match])
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

    row = data.get(date, None)
    if row is not None:
        return date, row

    if delta and limit_days != 0:
        return _find_closest_date(data, date + delta, limit_days - 1, delta, if_not_found)

    if if_not_found == "fail":
        raise DateNotFoundError("Data not found for date", date)
    if if_not_found == "nan":
        return date, float("NaN")

    raise ValueError(f"Invalid argument for if_not_found: {if_not_found}")


def _interval_to_years(interval_type: Literal["years", "months", "day"], interval_value: int) -> int:
    """Converts any time period to years for use with compounding functions"""

    year_conversion_factor = {"years": 1, "months": 12, "days": 365}
    years = interval_value / year_conversion_factor[interval_type]
    return years
