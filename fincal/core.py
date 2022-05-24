from __future__ import annotations

import datetime
import inspect
import warnings
from collections import UserList
from dataclasses import dataclass
from numbers import Number
from typing import Any, Callable, Iterable, List, Literal, Mapping, Sequence, Type
from unittest import skip

from dateutil.relativedelta import relativedelta

from .utils import FincalOptions, _parse_date, _preprocess_timeseries


@dataclass(frozen=True)
class Frequency:
    name: str
    freq_type: str
    value: int
    days: int
    symbol: str


def date_parser(*pos):
    """Decorator to parse dates in any function

        Accepts the 0-indexed position of the parameter for which date parsing needs to be done.
        Works even if function is used with keyword arguments while not maintaining parameter order.

    Example:
    --------
    >>> @date_parser(2, 3)
    >>> def calculate_difference(diff_units='days', return_type='int', date1, date2):
    ...     diff = date2 - date1
    ...     if return_type == 'int':
    ...         return diff.days
    ...     return diff
    ...
    >>> calculate_difference(date1='2019-01-01', date2='2020-01-01')
    datetime.timedelta(365)

    Each of the dates is automatically parsed into a datetime.datetime object from string.
    """

    def parse_dates(func):
        def wrapper_func(*args, **kwargs):
            date_format: str = kwargs.get("date_format", None)
            args: list = list(args)
            sig: inspect.Signature = inspect.signature(func)
            params: list = [i[0] for i in sig.parameters.items()]

            for j in pos:
                kwarg: str = params[j]
                date = kwargs.get(kwarg, None)
                in_args: bool = False
                if date is None:
                    try:
                        date = args[j]
                    except IndexError:
                        pass
                    in_args = True

                if date is None:
                    continue

                parsed_date: datetime.datetime = _parse_date(date, date_format)
                if not in_args:
                    kwargs[kwarg] = parsed_date
                else:
                    args[j] = parsed_date
            return func(*args, **kwargs)

        return wrapper_func

    return parse_dates


class AllFrequencies:
    D = Frequency("daily", "days", 1, 1, "D")
    W = Frequency("weekly", "days", 7, 7, "W")
    M = Frequency("monthly", "months", 1, 30, "M")
    Q = Frequency("quarterly", "months", 3, 91, "Q")
    H = Frequency("half-yearly", "months", 6, 182, "H")
    Y = Frequency("annual", "years", 1, 365, "Y")


class _IndexSlicer:
    """Class to create a slice using iloc in TimeSeriesCore"""

    def __init__(self, parent_obj: object):
        self.parent = parent_obj

    def __getitem__(self, n):
        if isinstance(n, int):
            keys: list = [self.parent.dates[n]]
        else:
            keys: list = self.parent.dates[n]
        item = [(key, self.parent.data[key]) for key in keys]
        if len(item) == 1:
            return item[0]

        return self.parent.__class__(item, self.parent.frequency.symbol)

    def __setitem__(self, key, value):
        raise NotImplementedError(
            "iloc cannot be used for setting a value as value will always be inserted in order of date"
        )


class Series(UserList):
    """Container for a series of objects, all objects must be of the same type"""

    def __init__(
        self,
        data: Sequence,
        dtype: Literal["date", "number", "bool"] = None,
        date_format: str = None,
    ):
        types_dict: dict = {
            "date": datetime.datetime,
            "datetime": datetime.datetime,
            "datetime.datetime": datetime.datetime,
            "float": float,
            "int": float,
            "number": float,
            "bool": bool,
            "Decimal": bool,
        }

        if not isinstance(data, Sequence):
            raise TypeError("Series object can only be created using Sequence types")

        if dtype is None:
            if isinstance(data[0], (Number, datetime.datetime, datetime.date, bool)):
                dtype = data[0].__class__.__name__.lower()

        if dtype not in types_dict.keys():
            raise ValueError("Unsupported value for data type")

        if dtype in ["date", "datetime", "datetime.datetime"]:
            data = [_parse_date(i, date_format) for i in data]
        else:
            func: Callable = types_dict[dtype]
            data: list = [func(i) for i in data]

        self.dtype: Type = types_dict[dtype]
        self.data: Sequence = data

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data}, data_type='{self.dtype.__name__}')"

    def __getitem__(self, i):
        if isinstance(i, slice):
            return self.__class__(self.data[i], str(self.dtype.__name__))
        else:
            return self.data[i]

    def _comparison_validator(self, other, skip_bool: bool = False):
        """Validates other before making comparison"""

        if isinstance(other, (str, datetime.datetime, datetime.date)):
            other = _parse_date(other)
            return other

        if self.dtype == bool and not skip_bool:
            raise TypeError("Comparison operation not supported for boolean series")

        elif isinstance(other, Series):
            if len(self) != len(other):
                raise ValueError("Length of Series must be same for comparison")

        elif (self.dtype != float and isinstance(other, Number)) or not isinstance(other, self.dtype):
            raise Exception(f"Cannot compare type {self.dtype.__name__} to {type(other).__name__}")

        return other

    def __gt__(self, other):
        other = self._comparison_validator(other)

        if isinstance(other, Series):
            return Series([j > other[i] for i, j in enumerate(self)], "bool")

        return Series([i > other for i in self.data], "bool")

    def __ge__(self, other):
        other = self._comparison_validator(other)

        if isinstance(other, Series):
            return Series([j >= other[i] for i, j in enumerate(self)], "bool")

        return Series([i >= other for i in self.data], "bool")

    def __lt__(self, other):
        other = self._comparison_validator(other)

        if isinstance(other, Series):
            return Series([j < other[i] for i, j in enumerate(self)], "bool")

        return Series([i < other for i in self.data], "bool")

    def __le__(self, other):
        other = self._comparison_validator(other)

        if isinstance(other, Series):
            return Series([j <= other[i] for i, j in enumerate(self)], "bool")

        return Series([i <= other for i in self.data], "bool")

    def __eq__(self, other):
        other = self._comparison_validator(other)

        if isinstance(other, Series):
            return Series([j == other[i] for i, j in enumerate(self)], "bool")

        return Series([i == other for i in self.data], "bool")

    def __ne__(self, other):
        other = self._comparison_validator(other)

        if isinstance(other, Series):
            return Series([j != other[i] for i, j in enumerate(self)], "bool")

        return Series([i != other for i in self.data], "bool")

    def __and__(self, other):
        other = self._comparison_validator(other, skip_bool=True)

        if isinstance(other, Series):
            return Series([j and other[i] for i, j in enumerate(self)], "bool")

        return Series([i and other for i in self.data], "bool")

    def __or__(self, other):
        other = self._comparison_validator(other, skip_bool=True)

        if isinstance(other, Series):
            return Series([j or other[i] for i, j in enumerate(self)], "bool")

        return Series([i or other for i in self.data], "bool")

    def _math_validator(self, other):

        if not isinstance(other, (Series, Number, datetime.timedelta, relativedelta, datetime.datetime, datetime.date)):
            return NotImplemented

        if isinstance(other, Series):
            if len(self) != len(other):
                raise ValueError("Arithmatic operations cannot be performed on objects of different lengths.")

            if self.dtype == bool or other.dtype == bool:
                raise TypeError("Arithmatic operations cannot be performed on boolean series.")

            if self.dtype == float and not other.dtype == float:
                raise TypeError(
                    "Arithmatic operation cannot be performed between "
                    f"'{self.dtype.__name__}' and '{other.dtype.__name__}'"
                )

            if self.dtype == datetime.datetime:
                raise TypeError(
                    "Arithmatic operation cannot be performed between '"
                    f"'{self.dtype.__name__}' and '{other.dtype.__name__}'"
                )

            return

        elif self.dtype == float and not isinstance(other, Number):
            raise TypeError(
                f"Arithmatic operation cannot be performed between '{self.dtype}' and '{other.__class__.__name__}'"
            )

        elif self.dtype == datetime.datetime and not isinstance(other, (datetime.timedelta, relativedelta)):
            raise TypeError(
                f"Arithmatic operation cannot be performed between '{self.dtype.__name__}' and "
                f"'{other.__class__.__name__}'\nHint: Try using timedelta or relativedelta objects."
            )

        return other

    def __add__(self, other):
        if self._math_validator(other) == NotImplemented:
            return NotImplemented

        if isinstance(other, Series):
            return self.__class__([j + other[i] for i, j in enumerate(self)], self.dtype.__name__)

        if isinstance(other, (Number, datetime.timedelta, relativedelta)):
            return self.__class__([i + other for i in self], self.dtype.__name__)


@Mapping.register
class TimeSeriesCore:
    """Defines the core building blocks of a TimeSeries object"""

    def __init__(
        self,
        ts_data: List[Iterable] | Mapping,
        frequency: Literal["D", "W", "M", "Q", "H", "Y"],
        date_format: str = "%Y-%m-%d",
    ):
        """Instantiate a TimeSeriesCore object

        Parameters
        ----------
        ts_data : List[Iterable] | Mapping
            Time Series data in the form of list of tuples or dictionary.
            The first element of each tuple should be a date and second element should be a value.
            In case of dictionary, the key should be the date.

        frequency : str
            The frequency of the time series.
            Valid values are {D, W, M, Q, H, Y}

        date_format : str, optional, default "%Y-%m-%d"
            Specify the format of the date
            Required only if the first argument of tuples is a string. Otherwise ignored.
        """

        ts_data = _preprocess_timeseries(ts_data, date_format=date_format)

        self.data = dict(ts_data)
        if len(self.data) != len(ts_data):
            warnings.warn("The input data contains duplicate dates which have been ignored.")
        self.frequency: Frequency = getattr(AllFrequencies, frequency)
        self.iter_num: int = -1
        self._dates: list = None
        self._values: list = None
        self._start_date: datetime.datetime = None
        self._end_date: datetime.datetime = None

    @property
    def dates(self) -> Series:
        """Get a list of all the dates in the TimeSeries object"""

        if self._dates is None or len(self._dates) != len(self.data):
            self._dates = list(self.data.keys())

        return Series(self._dates, "date")

    @property
    def values(self) -> Series:
        """Get a list of all the Values in the TimeSeries object"""

        if self._values is None or len(self._values) != len(self.data):
            self._values = list(self.data.values())

        return Series(self._values, "number")

    @property
    def start_date(self) -> datetime.datetime:
        """The first date in the TimeSeries object"""

        return self.dates[0]

    @property
    def end_date(self) -> datetime.datetime:
        """The last date in the TimeSeries object"""

        return self.dates[-1]

    def _get_printable_slice(self, n: int):
        """Helper function for __repr__ and __str__

        Returns a slice of the dataframe from beginning and end.
        """

        printable = {}
        iter_f = iter(self.data)
        first_n = [next(iter_f) for i in range(n // 2)]

        iter_b = reversed(self.data)
        last_n = [next(iter_b) for i in range(n // 2)]
        last_n.sort()

        printable["start"] = [str((i, self.data[i])) for i in first_n]
        printable["end"] = [str((i, self.data[i])) for i in last_n]
        return printable

    def __repr__(self):
        if len(self.data) > 6:
            printable = self._get_printable_slice(6)
            printable_str = "{}([{}\n\t    ...\n\t    {}], frequency={})".format(
                self.__class__.__name__,
                ",\n\t    ".join(printable["start"]),
                ",\n\t    ".join(printable["end"]),
                repr(self.frequency.symbol),
            )
        else:
            printable_str = "{}([{}], frequency={})".format(
                self.__class__.__name__,
                ",\n\t".join([str(i) for i in self.data.items()]),
                repr(self.frequency.symbol),
            )
        return printable_str

    def __str__(self):
        if len(self.data) > 6:
            printable = self._get_printable_slice(6)
            printable_str = "[{}\n ...\n {}]".format(
                ",\n ".join(printable["start"]),
                ",\n ".join(printable["end"]),
            )
        else:
            printable_str = "[{}]".format(",\n ".join([str(i) for i in self.data.items()]))
        return printable_str

    @date_parser(1)
    def _get_item_from_date(self, date: str | datetime.datetime):
        """Helper function to retrieve item using a date"""

        return self.get(date, raise_error=True)

    def _get_item_from_key(self, key: str | datetime.datetime):
        """Helper function to implement special keys"""

        if isinstance(key, int):
            raise KeyError(f"{key}. \nHint: use .iloc[{key}] for index based slicing.")

        if key in ["dates", "values"]:
            return getattr(self, key)

        return self._get_item_from_date(key)

    def _get_item_from_list(self, date_list: Sequence[str | datetime.datetime]):
        """Helper function to retrieve items using a list"""

        data_to_return = [self._get_item_from_key(key) for key in date_list]
        return self.__class__(data_to_return, frequency=self.frequency.symbol)

    def _get_item_from_series(self, series: Series):
        """Helper function to retrieve item using a Series object

        A Series of type bool of equal length to the time series can be used.
        A Series of dates can be used to filter out a set of dates.
        """
        if series.dtype == bool:
            if len(series) != len(self.dates):
                raise ValueError(f"Length of Series: {len(series)} did not match length of object: {len(self.dates)}")
            dates_to_return = [self.dates[i] for i, j in enumerate(series) if j]
        elif series.dtype == datetime.datetime:
            dates_to_return = list(series)
        else:
            raise TypeError(f"Cannot slice {self.__class__.__name__} using a Series of {series.dtype.__name__}")

        return self._get_item_from_list(dates_to_return)

    def __getitem__(self, key):
        if isinstance(key, (int, str, datetime.datetime, datetime.date)):
            return self._get_item_from_key(key)

        if isinstance(key, Series):
            return self._get_item_from_series(key)

        if isinstance(key, Sequence):
            return self._get_item_from_list(key)

        raise TypeError(f"Invalid type {repr(type(key).__name__)} for slicing.")

    @date_parser(1)
    def __setitem__(self, key: str | datetime.datetime, value: Number) -> None:
        if not isinstance(value, Number):
            raise TypeError("Only numerical values can be stored in TimeSeries")

        if key in self.data:
            self.data[key] = float(value)
        else:
            self.data.update({key: float(value)})
            self.data = dict(sorted(self.data.items()))

    @date_parser(1)
    def __delitem__(self, key):
        del self.data[key]

    def _comparison_validator(self, other):
        """Validates the data before comparison is performed"""

        if not isinstance(other, (Number, Series, TimeSeriesCore)):
            raise TypeError(
                f"Comparison cannot be performed between '{self.__class__.__name__}' and '{other.__class__.__name__}'"
            )

        if isinstance(other, TimeSeriesCore):
            if any(self.dates != other.dates):
                raise ValueError(
                    "Only objects with same set of dates can be compared.\n"
                    "Hint: use TimeSeries.sync() method to sync dates of two TimeSeries objects."
                )

        if isinstance(other, Series):
            if other.dtype != float:
                raise TypeError("Only Series of type float can be used for comparison")

            if len(self) != len(other):
                raise ValueError("Length of series does not match length of object")

    def __gt__(self, other):
        self._comparison_validator(other)

        if isinstance(other, Number):
            data = {k: v > other for k, v in self.data.items()}

        if isinstance(other, TimeSeriesCore):
            data = {dt: val > other[dt][1] for dt, val in self.data.items()}

        if isinstance(other, Series):
            data = {dt: val > other[i] for i, (dt, val) in enumerate(self.data.items())}

        return self.__class__(data, frequency=self.frequency.symbol)

    def __ge__(self, other):
        self._comparison_validator(other)

        if isinstance(other, Number):
            data = {k: v >= other for k, v in self.data.items()}

        if isinstance(other, TimeSeriesCore):
            data = {dt: val >= other[dt][1] for dt, val in self.data.items()}

        if isinstance(other, Series):
            data = {dt: val >= other[i] for i, (dt, val) in enumerate(self.data.items())}

        return self.__class__(data, frequency=self.frequency.symbol)

    def __lt__(self, other):
        self._comparison_validator(other)

        if isinstance(other, Number):
            data = {k: v < other for k, v in self.data.items()}

        if isinstance(other, TimeSeriesCore):
            data = {dt: val < other[dt][1] for dt, val in self.data.items()}

        if isinstance(other, Series):
            data = {dt: val < other[i] for i, (dt, val) in enumerate(self.data.items())}

        return self.__class__(data, frequency=self.frequency.symbol)

    def __le__(self, other):
        self._comparison_validator(other)

        if isinstance(other, Number):
            data = {k: v <= other for k, v in self.data.items()}

        if isinstance(other, TimeSeriesCore):
            data = {dt: val <= other[dt][1] for dt, val in self.data.items()}

        if isinstance(other, Series):
            data = {dt: val <= other[i] for i, (dt, val) in enumerate(self.data.items())}

        return self.__class__(data, frequency=self.frequency.symbol)

    def __eq__(self, other):
        self._comparison_validator(other)

        if isinstance(other, Number):
            data = {k: v == other for k, v in self.data.items()}

        if isinstance(other, TimeSeriesCore):
            data = {dt: val == other[dt][1] for dt, val in self.data.items()}

        if isinstance(other, Series):
            data = {dt: val == other[i] for i, (dt, val) in enumerate(self.data.items())}

        return self.__class__(data, frequency=self.frequency.symbol)

    def __ne__(self, other):
        self._comparison_validator(other)

        if isinstance(other, Number):
            data = {k: v != other for k, v in self.data.items()}

        if isinstance(other, TimeSeriesCore):
            data = {dt: val != other[dt][1] for dt, val in self.data.items()}

        if isinstance(other, Series):
            data = {dt: val != other[i] for i, (dt, val) in enumerate(self.data.items())}

        return self.__class__(data, frequency=self.frequency.symbol)

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if self.n >= len(self.dates):
            raise StopIteration
        else:
            key = self.dates[self.n]
            self.n += 1
            return key, self.data[key]

    def __len__(self):
        return len(self.data)

    @date_parser(1)
    def __contains__(self, key: object) -> bool:
        return key in self.data

    def _arithmatic_validator(self, other):
        """Validates input data before performing math operatios"""

        if not isinstance(other, (Number, Series, TimeSeriesCore)):
            raise TypeError(
                "Cannot perform mathematical operations between "
                f"'{self.__class__.__name__}' and '{other.__class__.__name__}'"
            )

        if isinstance(other, TimeSeriesCore):
            if len(other) != len(self):
                raise ValueError("Can only perform mathematical operations between objects of same length.")
            if any(self.dates != other.dates):
                raise ValueError("Can only perform mathematical operations between objects having same dates.")

        if isinstance(other, Series):
            if other.dtype != float:
                raise TypeError(
                    "Cannot perform mathematical operations with "
                    f"'{other.__class__.__name__}' of type '{other.dtype}'"
                )
            if len(other) != len(self):
                raise ValueError("Can only perform mathematical operations between objects of same length.")

    def __add__(self, other):
        self._arithmatic_validator(other)

        if isinstance(other, TimeSeriesCore):
            other = other.values

        if isinstance(other, Series):
            data = {dt: val + other[i] for i, (dt, val) in enumerate(self.data.items())}
        elif isinstance(other, Number):
            data = {dt: val + other for dt, val in self.data.items()}

        return self.__class__(data, self.frequency.symbol)

    def __sub__(self, other):
        self._arithmatic_validator(other)

        if isinstance(other, TimeSeriesCore):
            other = other.values

        if isinstance(other, Series):
            data = {dt: val - other[i] for i, (dt, val) in enumerate(self.data.items())}
        elif isinstance(other, Number):
            data = {dt: val - other for dt, val in self.data.items()}

        return self.__class__(data, self.frequency.symbol)

    def __truediv__(self, other):
        self._arithmatic_validator(other)

        if isinstance(other, TimeSeriesCore):
            other = other.values

        if isinstance(other, Series):
            data = {dt: val / other[i] for i, (dt, val) in enumerate(self.data.items())}
        elif isinstance(other, Number):
            data = {dt: val / other for dt, val in self.data.items()}

        return self.__class__(data, self.frequency.symbol)

    def __floordiv__(self, other):
        self._arithmatic_validator(other)

        if isinstance(other, TimeSeriesCore):
            other = other.values

        if isinstance(other, Series):
            data = {dt: val // other[i] for i, (dt, val) in enumerate(self.data.items())}
        elif isinstance(other, Number):
            data = {dt: val // other for dt, val in self.data.items()}

        return self.__class__(data, self.frequency.symbol)

    def __mul__(self, other):
        self._arithmatic_validator(other)

        if isinstance(other, TimeSeriesCore):
            other = other.values

        if isinstance(other, Series):
            data = {dt: val * other[i] for i, (dt, val) in enumerate(self.data.items())}
        elif isinstance(other, Number):
            data = {dt: val * other for dt, val in self.data.items()}

        return self.__class__(data, self.frequency.symbol)

    def __mod__(self, other):
        self._arithmatic_validator(other)

        if isinstance(other, TimeSeriesCore):
            other = other.values

        if isinstance(other, Series):
            data = {dt: val % other[i] for i, (dt, val) in enumerate(self.data.items())}
        elif isinstance(other, Number):
            data = {dt: val % other for dt, val in self.data.items()}

        return self.__class__(data, self.frequency.symbol)

    def __pow__(self, other):
        self._arithmatic_validator(other)

        if isinstance(other, TimeSeriesCore):
            other = other.values

        if isinstance(other, Series):
            data = {dt: val ** other[i] for i, (dt, val) in enumerate(self.data.items())}
        elif isinstance(other, Number):
            data = {dt: val**other for dt, val in self.data.items()}

        return self.__class__(data, self.frequency.symbol)

    def __radd__(self, other):
        self._arithmatic_validator(other)

        if isinstance(other, TimeSeriesCore):
            other = other.values

        if isinstance(other, Series):
            data = {dt: val + other[i] for i, (dt, val) in enumerate(self.data.items())}
        elif isinstance(other, Number):
            data = {dt: val + other for dt, val in self.data.items()}

        return self.__class__(data, self.frequency.symbol)

    def __rsub__(self, other):
        self._arithmatic_validator(other)

        if isinstance(other, TimeSeriesCore):
            other = other.values

        if isinstance(other, Series):
            data = {dt: other[i] - val for i, (dt, val) in enumerate(self.data.items())}
        elif isinstance(other, Number):
            data = {dt: other - val for dt, val in self.data.items()}

        return self.__class__(data, self.frequency.symbol)

    def __rtruediv__(self, other):
        self._arithmatic_validator(other)

        if isinstance(other, TimeSeriesCore):
            other = other.values

        if isinstance(other, Series):
            data = {dt: other[i] / val for i, (dt, val) in enumerate(self.data.items())}
        elif isinstance(other, Number):
            data = {dt: other / val for dt, val in self.data.items()}

        return self.__class__(data, self.frequency.symbol)

    def __rfloordiv__(self, other):
        self._arithmatic_validator(other)

        if isinstance(other, TimeSeriesCore):
            other = other.values

        if isinstance(other, Series):
            data = {dt: other[i] // val for i, (dt, val) in enumerate(self.data.items())}
        elif isinstance(other, Number):
            data = {dt: other // val for dt, val in self.data.items()}

        return self.__class__(data, self.frequency.symbol)

    def __rmul__(self, other):
        self._arithmatic_validator(other)

        if isinstance(other, TimeSeriesCore):
            other = other.values

        if isinstance(other, Series):
            data = {dt: val * other[i] for i, (dt, val) in enumerate(self.data.items())}
        elif isinstance(other, Number):
            data = {dt: val * other for dt, val in self.data.items()}

        return self.__class__(data, self.frequency.symbol)

    def __rpow__(self, _):
        raise NotImplementedError("This operation is not supported.")

    @date_parser(1)
    def get(
        self,
        date: str | datetime.datetime,
        default: Any = None,
        closest: Literal["previous", "next"] = None,
        limit: int = 1000,
        raise_error: bool = False,
    ) -> tuple | Any:
        """Get a value for a particular key. Return a default value on KeyError

        Parameters
        ----------
        date:
            Date for which the value needs to be fetched.

        default: Optional, Default None
            Default value to be returned in case the date is not found. Default None.

        closest:
            Look for previous or next value when date is not found.
            If not specified, the value set in FincalOptions is used

        limit:
            Maximum number of days to look for the closest available date.
            If exceeded without finding a date, default value will be returned.

        raise_error : bool, optional
            Whether to raise an error and ignore the default value.
            Meant for use with __getitem__.

        Returns
        -------
        tuple | Any
            _description_

        Raises
        ------
        ValueError
            If the argument for closest is not valid.

        KeyError
            if raise_error is true and date is not found
        """

        if closest is None:
            closest = FincalOptions.get_closest

        time_delta_dict = {"exact": 0, "previous": -1, "next": 1}

        if closest not in time_delta_dict:
            raise ValueError(f"Invalid argument from closest {closest!r}")
        delta = relativedelta(days=time_delta_dict[closest])

        for _ in range(limit):
            try:
                return date, self.data[date]
            except KeyError:
                if not delta:
                    break
                date += delta

        if raise_error:
            raise KeyError(date)
        return default

    @property
    def iloc(self) -> Mapping:
        """Returns an item or a set of items based on index

            supports slicing using numerical index.
            Accepts integers or Python slice objects

        Usage
        -----
        >>> ts = TimeSeries(data, frequency='D')
        >>> ts.iloc[0]  # get the first value
        >>> ts.iloc[-1]  # get the last value
        >>> ts.iloc[:3]  # get the first 3 values
        >>> ts.illoc[-3:]  # get the last 3 values
        >>> ts.iloc[5:10]  # get five values starting from the fifth value
        >>> ts.iloc[::2]  # get every alternate date
        """

        return _IndexSlicer(self)

    def head(self, n: int = 6) -> TimeSeriesCore:
        """Returns the first n items of the TimeSeries object"""

        return self.iloc[:n]

    def tail(self, n: int = 6) -> TimeSeriesCore:
        """Returns the last n items of the TimeSeries object"""

        return self.iloc[-n:]

    def items(self):
        return self.data.items()

    def update(self, items: dict):
        for k, v in items.items():
            self[k] = v
