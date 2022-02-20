import datetime
from dataclasses import dataclass
from msilib import sequence
from typing import Dict, Iterable, List, Literal, Mapping, Sequence, Tuple, Union


@dataclass
class Options:
    date_format: str = '%Y-%m-%d'
    closest: str = 'before'  # after


@dataclass(frozen=True)
class Frequency:
    name: str
    freq_type: str
    value: int
    days: int


class AllFrequencies:
    D = Frequency('daily', 'days', 1, 1)
    W = Frequency('weekly', 'days', 7, 7)
    M = Frequency('monthly', 'months', 1, 30)
    Q = Frequency('quarterly', 'months', 3, 91)
    H = Frequency('half-yearly', 'months', 6, 182)
    Y = Frequency('annual', 'years', 1, 365)


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


class TimeSeriesCore:
    """Defines the core building blocks of a TimeSeries object"""

    def __init__(
        self,
        data: List[Iterable],
        date_format: str = "%Y-%m-%d",
        frequency=Literal['D', 'W', 'M', 'Q', 'H', 'Y']
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
        self.dates = list(self.time_series)
        if len(self.time_series) != len(data):
            print("Warning: The input data contains duplicate dates which have been ignored.")
        self.start_date = self.dates[0]
        self.end_date = self.dates[-1]
        self.frequency = getattr(AllFrequencies, frequency)

    def __repr__(self):
        if len(self.time_series) > 6:
            printable_data_1 = list(self.time_series)[:3]
            printable_data_2 = list(self.time_series)[-3:]
            printable_str = "TimeSeries([{}\n\t...\n\t{}])".format(
                                ',\n\t'.join([str((i, self.time_series[i])) for i in printable_data_1]),
                                ',\n\t'.join([str((i, self.time_series[i])) for i in printable_data_2])
                                )
        else:
            printable_data = self.time_series
            printable_str = "TimeSeries([{}])".format(',\n\t'.join(
                                [str((i, self.time_series[i])) for i in printable_data]))
        return printable_str

    def __str__(self):
        if len(self.time_series) > 6:
            printable_data_1 = list(self.time_series)[:3]
            printable_data_2 = list(self.time_series)[-3:]
            printable_str = "[{}\n ...\n {}]".format(
                                ',\n '.join([str((i, self.time_series[i])) for i in printable_data_1]),
                                ',\n '.join([str((i, self.time_series[i])) for i in printable_data_2])
                                )
        else:
            printable_data = self.time_series
            printable_str = "[{}]".format(',\n '.join([str((i, self.time_series[i])) for i in printable_data]))
        return printable_str

    def __getitem__(self, n):
        all_keys = list(self.time_series.keys())
        if isinstance(n, int):
            keys = [all_keys[n]]
        else:
            keys = all_keys[n]
        item = [(key, self.time_series[key]) for key in keys]
        if len(item) == 1:
            return item[0]

        return item

    def __len__(self):
        return len(self.time_series.keys())

    def head(self, n: int = 6):
        keys = list(self.time_series.keys())
        keys = keys[:n]
        result = [(key, self.time_series[key]) for key in keys]
        return result

    def tail(self, n: int = 6):
        keys = list(self.time_series.keys())
        keys = keys[-n:]
        result = [(key, self.time_series[key]) for key in keys]
        return result
