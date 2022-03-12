import datetime
import inspect
from collections import UserDict, UserList
from dataclasses import dataclass
from numbers import Number
from typing import Iterable, List, Literal, Mapping, Sequence, Union

from .utils import _parse_date, _preprocess_timeseries


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
            date_format = kwargs.get("date_format", None)
            args = list(args)
            sig = inspect.signature(func)
            params = [i[0] for i in sig.parameters.items()]

            for j in pos:
                kwarg = params[j]
                date = kwargs.get(kwarg, None)
                in_args = False
                if date is None:
                    try:
                        date = args[j]
                    except IndexError:
                        pass
                    in_args = True

                if date is None:
                    continue

                parsed_date = _parse_date(date, date_format)
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
            keys = [self.parent.dates[n]]
        else:
            keys = self.parent.dates[n]
        item = [(key, self.parent.data[key]) for key in keys]
        if len(item) == 1:
            return item[0]

        return self.parent.__class__(item, self.parent.frequency.symbol)


class Series(UserList):
    """Container for a series of objects, all objects must be of the same type"""

    def __init__(
        self,
        data,
        data_type: Literal["date", "number", "bool"],
        date_format: str = None,
    ):
        types_dict = {
            "date": datetime.datetime,
            "datetime": datetime.datetime,
            "datetime.datetime": datetime.datetime,
            "float": float,
            "int": float,
            "number": float,
            "bool": bool,
        }

        if data_type not in types_dict.keys():
            raise ValueError("Unsupported value for data type")

        if not isinstance(data, Sequence):
            raise TypeError("Series object can only be created using Sequence types")

        if data_type in ["date", "datetime", "datetime.datetime"]:
            data = [_parse_date(i, date_format) for i in data]
        else:
            func = types_dict[data_type]
            data = [func(i) for i in data]

        self.dtype = types_dict[data_type]
        self.data = data

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data}, data_type='{self.dtype.__name__}')"

    def __getitem__(self, i):
        if isinstance(i, slice):
            return self.__class__(self.data[i], str(self.dtype.__name__))
        else:
            return self.data[i]

    def __gt__(self, other):
        if self.dtype == bool:
            raise TypeError("> not supported for boolean series")

        if isinstance(other, (str, datetime.datetime, datetime.date)):
            other = _parse_date(other)

        if self.dtype == float and isinstance(other, Number) or isinstance(other, self.dtype):
            gt = Series([i > other for i in self.data], "bool")
        else:
            raise Exception(f"Cannot compare type {self.dtype.__name__} to {type(other).__name__}")

        return gt

    def __ge__(self, other):
        if self.dtype == bool:
            raise TypeError(">= not supported for boolean series")

        if isinstance(other, (str, datetime.datetime, datetime.date)):
            other = _parse_date(other)

        if self.dtype == float and isinstance(other, Number) or isinstance(other, self.dtype):
            ge = Series([i >= other for i in self.data], "bool")
        else:
            raise Exception(f"Cannot compare type {self.dtype.__name__} to {type(other).__name__}")

        return ge

    def __lt__(self, other):
        if self.dtype == bool:
            raise TypeError("< not supported for boolean series")

        if isinstance(other, (str, datetime.datetime, datetime.date)):
            other = _parse_date(other)

        if self.dtype == float and isinstance(other, Number) or isinstance(other, self.dtype):
            lt = Series([i < other for i in self.data], "bool")
        else:
            raise Exception(f"Cannot compare type {self.dtype.__name__} to {type(other).__name__}")
        return lt

    def __le__(self, other):
        if self.dtype == bool:
            raise TypeError("<= not supported for boolean series")

        if isinstance(other, (str, datetime.datetime, datetime.date)):
            other = _parse_date(other)

        if self.dtype == float and isinstance(other, Number) or isinstance(other, self.dtype):
            le = Series([i <= other for i in self.data], "bool")
        else:
            raise Exception(f"Cannot compare type {self.dtype.__name__} to {type(other).__name__}")
        return le

    def __eq__(self, other):
        if isinstance(other, (str, datetime.datetime, datetime.date)):
            other = _parse_date(other)

        if self.dtype == float and isinstance(other, Number) or isinstance(other, self.dtype):
            eq = Series([i == other for i in self.data], "bool")
        else:
            raise Exception(f"Cannot compare type {self.dtype.__name__} to {type(other).__name__}")
        return eq


class TimeSeriesCore(UserDict):
    """Defines the core building blocks of a TimeSeries object"""

    def __init__(
        self, data: List[Iterable], frequency: Literal["D", "W", "M", "Q", "H", "Y"], date_format: str = "%Y-%m-%d"
    ):
        """Instantiate a TimeSeriesCore object

        Parameters
        ----------
        data : List[tuple]
            Time Series data in the form of list of tuples.
            The first element of each tuple should be a date and second element should be a value.

        date_format : str, optional, default "%Y-%m-%d"
            Specify the format of the date
            Required only if the first argument of tuples is a string. Otherwise ignored.

        frequency : str, optional, default "infer"
            The frequency of the time series. Default is infer.
            The class will try to infer the frequency automatically and adjust to the closest member.
            Note that inferring frequencies can fail if the data is too irregular.
            Valid values are {D, W, M, Q, H, Y}
        """

        data = _preprocess_timeseries(data, date_format=date_format)

        self.data = dict(data)
        if len(self.data) != len(data):
            print("Warning: The input data contains duplicate dates which have been ignored.")
        self.frequency = getattr(AllFrequencies, frequency)
        self.iter_num = -1
        self._dates = None
        self._values = None
        self._start_date = None
        self._end_date = None

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
    def _get_item_from_date(self, date: Union[str, datetime.datetime]):
        return date, self.data[date]

    def _get_item_from_key(self, key: Union[str, datetime.datetime]):
        if isinstance(key, int):
            raise KeyError(f"{key}. \nHint: use .iloc[{key}] for index based slicing.")

        if key in ["dates", "values"]:
            return getattr(self, key)

        return self._get_item_from_date(key)

    def _get_item_from_list(self, date_list: Sequence[Union[str, datetime.datetime]]):
        data_to_return = [self._get_item_from_key(key) for key in date_list]
        return self.__class__(data_to_return, frequency=self.frequency.symbol)

    def _get_item_from_series(self, series: Series):
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

    @date_parser(1)
    def __contains__(self, key: object) -> bool:
        return super().__contains__(key)

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

    def head(self, n: int = 6):
        """Returns the first n items of the TimeSeries object"""

        return self.iloc[:n]

    def tail(self, n: int = 6):
        """Returns the last n items of the TimeSeries object"""

        return self.iloc[-n:]

    def items(self):
        return self.data.items()
