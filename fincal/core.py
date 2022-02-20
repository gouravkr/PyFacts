import datetime
from dataclasses import dataclass
from numbers import Number
from typing import Iterable, List, Literal, Mapping, Sequence, Tuple, Union


@dataclass
class FincalOptions:
    date_format: str = '%Y-%m-%d'
    closest: str = 'before'  # after


@dataclass(frozen=True)
class Frequency:
    name: str
    freq_type: str
    value: int
    days: int
    symbol: str


class AllFrequencies:
    D = Frequency('daily', 'days', 1, 1, 'D')
    W = Frequency('weekly', 'days', 7, 7, 'W')
    M = Frequency('monthly', 'months', 1, 30, 'M')
    Q = Frequency('quarterly', 'months', 3, 91, 'Q')
    H = Frequency('half-yearly', 'months', 6, 182, 'H')
    Y = Frequency('annual', 'years', 1, 365, 'Y')


def _preprocess_timeseries(
    data: Union[
        Sequence[Iterable[Union[str, datetime.datetime, float]]],
        Sequence[Mapping[str, Union[float, datetime.datetime]]],
        Sequence[Mapping[Union[str, datetime.datetime], float]],
        Mapping[Union[str, datetime.datetime], float]
    ],
    date_format: str
) -> List[Tuple[datetime.datetime, float]]:
    """Converts any type of list to the correct type"""

    if isinstance(data, Sequence):
        if isinstance(data[0], Mapping):
            if len(data[0].keys()) == 2:
                current_data = [tuple(i.values()) for i in data]
            elif len(data[0].keys()) == 1:
                current_data = [tuple(*i.items()) for i in data]
            else:
                raise TypeError("Could not parse the data")
            current_data = _preprocess_timeseries(current_data, date_format)

        elif isinstance(data[0], Sequence):
            if isinstance(data[0][0], str):
                current_data = []
                for i in data:
                    row = datetime.datetime.strptime(i[0], date_format), i[1]
                    current_data.append(row)
            elif isinstance(data[0][0], datetime.datetime):
                current_data = [(i, j) for i, j in data]
            else:
                raise TypeError("Could not parse the data")
        else:
            raise TypeError("Could not parse the data")

    elif isinstance(data, Mapping):
        current_data = [(k, v) for k, v in data.items()]
        current_data = _preprocess_timeseries(current_data, date_format)

    else:
        raise TypeError("Could not parse the data")
    current_data.sort()
    return current_data


def _preprocess_match_options(as_on_match: str, prior_match: str, closest: str) -> datetime.timedelta:
    """Checks the arguments and returns appropriate timedelta objects"""

    deltas = {'exact': 0, 'previous': -1, 'next': 1}
    if closest not in deltas.keys():
        raise ValueError(f"Invalid closest argument: {closest}")

    as_on_match = closest if as_on_match == 'closest' else as_on_match
    prior_match = closest if prior_match == 'closest' else prior_match

    if as_on_match in deltas.keys():
        as_on_delta = datetime.timedelta(days=deltas[as_on_match])
    else:
        raise ValueError(f"Invalid as_on_match argument: {as_on_match}")

    if prior_match in deltas.keys():
        prior_delta = datetime.timedelta(days=deltas[prior_match])
    else:
        raise ValueError(f"Invalid prior_match argument: {prior_match}")

    return as_on_delta, prior_delta


class IndexSlicer:
    def __init__(self, parent_obj):
        self.parent = parent_obj

    def __getitem__(self, n):
        all_keys = list(self.parent.time_series)
        if isinstance(n, int):
            keys = [all_keys[n]]
        else:
            keys = all_keys[n]
        item = [(key, self.parent.time_series[key]) for key in keys]
        if len(item) == 1:
            return item[0]

        return item


class Series:
    def __init__(self, data):
        if not isinstance(data, Sequence):
            raise TypeError("Series only supports creation using Sequence types")

        if isinstance(data[0], bool):
            self.data = data
            self.dtype = bool
        elif isinstance(data[0], Number):
            self.dtype = float
            self.data = [float(i) for i in data]
        elif isinstance(data[0], str):
            try:
                data = [datetime.datetime.strptime(i, FincalOptions.date_format) for i in data]
                self.dtype = datetime.datetime
            except ValueError:
                raise TypeError("Series does not support string data type")
        elif isinstance(data[0], datetime.datetime):
            self.dtype = datetime.datetime
            self.data = data
        else:
            raise TypeError(f"Cannot create series object from {type(data).__name__} of {type(data[0]).__name__}")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data})"

    def __getitem__(self, n):
        return self.data[n]

    def __len__(self):
        return len(self.data)

    def __gt__(self, other):
        if self.dtype == bool:
            raise TypeError("> not supported for boolean series")

        if self.dtype == float and isinstance(other, Number) or isinstance(other, self.dtype):
            gt = Series([i > other for i in self.data])
        else:
            raise Exception(f"Cannot compare type {self.dtype.__name__} to {type(other).__name__}")

        return gt

    def __lt__(self, other):
        if self.dtype == bool:
            raise TypeError("< not supported for boolean series")

        if self.dtype == float and isinstance(other, Number) or isinstance(other, self.dtype):
            lt = Series([i < other for i in self.data])
        else:
            raise Exception(f"Cannot compare type {self.dtype.__name__} to {type(other).__name__}")
        return lt

    def __eq__(self, other):
        if self.dtype == float and isinstance(other, Number) or isinstance(other, self.dtype):
            eq = Series([i == other for i in self.data])
        else:
            raise Exception(f"Cannot compare type {self.dtype.__name__} to {type(other).__name__}")
        return eq


class TimeSeriesCore:
    """Defines the core building blocks of a TimeSeries object"""

    def __init__(
        self,
        data: List[Iterable],
        frequency: Literal['D', 'W', 'M', 'Q', 'H', 'Y'],
        date_format: str = "%Y-%m-%d"
    ):
        """Instantiate a TimeSeries object

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

        self.time_series = dict(data)
        if len(self.time_series) != len(data):
            print("Warning: The input data contains duplicate dates which have been ignored.")
        self.frequency = getattr(AllFrequencies, frequency)
        self.iter_num = -1
        self._dates = None
        self._values = None
        self._start_date = None
        self._end_date = None

    @property
    def dates(self):
        if self._dates is None or len(self._dates) != len(self.time_series):
            self._dates = list(self.time_series.keys())

        return Series(self._dates)

    @property
    def values(self):
        if self._values is None or len(self._values) != len(self.time_series):
            self._values = list(self.time_series.values())

        return Series(self._values)

    @property
    def start_date(self):
        return self.dates[0]

    @property
    def end_date(self):
        return self.dates[-1]

    def _get_printable_slice(self, n: int):
        """Returns a slice of the dataframe from beginning and end"""

        printable = {}
        iter_f = iter(self.time_series)
        first_n = [next(iter_f) for i in range(n//2)]

        iter_b = reversed(self.time_series)
        last_n = [next(iter_b) for i in range(n//2)]
        last_n.sort()

        printable['start'] = [str((i, self.time_series[i])) for i in first_n]
        printable['end'] = [str((i, self.time_series[i])) for i in last_n]
        return printable

    def __repr__(self):
        if len(self.time_series) > 6:
            printable = self._get_printable_slice(6)
            printable_str = "{}([{}\n\t    ...\n\t    {}], frequency={})".format(
                                self.__class__.__name__,
                                ',\n\t    '.join(printable['start']),
                                ',\n\t    '.join(printable['end']),
                                repr(self.frequency.symbol)
                                )
        else:
            printable_str = "{}([{}], frequency={})".format(
                                              self.__class__.__name__,
                                              ',\n\t'.join([str(i) for i in self.time_series.items()]),
                                              repr(self.frequency.symbol)
                                             )
        return printable_str

    def __str__(self):
        if len(self.time_series) > 6:
            printable = self._get_printable_slice(6)
            printable_str = "[{}\n ...\n {}]".format(
                                ',\n '.join(printable['start']),
                                ',\n '.join(printable['end']),
                                )
        else:
            printable_str = "[{}]".format(',\n '.join([str(i) for i in self.time_series.items()]))
        return printable_str

    def __getitem__(self, key):
        if isinstance(key, Series):
            if not key.dtype == bool:
                raise ValueError(f"Cannot slice {self.__class__.__name__} using a Series of {key.dtype.__name__}")
            elif len(key) != len(self.dates):
                raise Exception(f"Length of Series: {len(key)} did not match length of object: {len(self.dates)}")
            else:
                dates_to_return = [self.dates[i] for i, j in enumerate(key) if j]
                data_to_return = [(key, self.time_series[key]) for key in dates_to_return]
                return TimeSeriesCore(data_to_return)

        if isinstance(key, int):
            raise KeyError(f"{key}. For index based slicing, use .iloc[{key}]")
        elif isinstance(key, datetime.datetime):
            item = (key, self.time_series[key])
        if isinstance(key, str):
            if key == 'dates':
                return self.dates
            elif key == 'values':
                return list(self.time_series.values())
            try:
                dt_key = datetime.datetime.strptime(key, FincalOptions.date_format)
                item = (dt_key, self.time_series[dt_key])
            except ValueError:
                raise KeyError(f"{repr(key)}. If you passed a date as a string, "
                               "try setting the date format using Fincal.Options.date_format")
            except KeyError:
                raise KeyError(f"{repr(key)}. This date is not available.")
        elif isinstance(key, Sequence):
            item = [(k, self.time_series[k]) for k in key]
        else:
            raise TypeError(f"Invalid type {repr(type(key).__name__)} for slicing.")
        return item

    def __len__(self):
        return len(self.time_series)

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if self.n >= len(self.dates):
            raise StopIteration
        else:
            key = self.dates[self.n]
            self.n += 1
            return key, self.time_series[key]

    def head(self, n: int = 6):
        """Returns the first n items of the TimeSeries object"""

        keys = list(self.time_series.keys())
        keys = keys[:n]
        result = [(key, self.time_series[key]) for key in keys]
        return result

    def tail(self, n: int = 6):
        """Returns the last n items of the TimeSeries object"""

        keys = list(self.time_series.keys())
        keys = keys[-n:]
        result = [(key, self.time_series[key]) for key in keys]
        return result

    @property
    def iloc(self):
        """Returns an item or a set of items based on index"""

        return IndexSlicer(self)
