import datetime
from dataclasses import dataclass
from typing import Dict, Iterable, List, Literal, Tuple, Union

from dateutil.relativedelta import relativedelta


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


def create_date_series(
    start_date: datetime.datetime,
    end_date: datetime.datetime,
    frequency: Frequency
) -> List[datetime.datetime]:
    """Creates a date series using a frequency"""

    print(f"{start_date=}, {end_date=}")
    datediff = (end_date - start_date).days/frequency.days+1
    dates = []

    for i in range(0, int(datediff)):
        diff = {frequency.freq_type: frequency.value*i}
        dates.append(start_date + relativedelta(**diff))

    return dates


def _preprocess_timeseries(
    data: Union[
        List[Iterable[Union[str, datetime.datetime, float]]],
        List[Dict[str, Union[float, datetime.datetime]]],
        List[Dict[Union[str, datetime.datetime], float]],
        Dict[Union[str, datetime.datetime], float]
    ],
    date_format: str
) -> List[Tuple[datetime.datetime, float]]:
    """Converts any type of list to the correct type"""

    if isinstance(data, list):
        if isinstance(data[0], dict):
            if len(data[0].keys()) == 2:
                current_data = [tuple(i.values()) for i in data]
            elif len(data[0].keys()) == 1:
                current_data = [tuple(*i.items()) for i in data]
            else:
                raise TypeError("Could not parse the data")
            current_data = _preprocess_timeseries(current_data, date_format)

        elif isinstance(data[0], Iterable):
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

    elif isinstance(data, dict):
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
        self.dates = set(list(self.time_series))
        if len(self.dates) != len(data):
            print("Warning: The input data contains duplicate dates which have been ignored.")
        self.start_date = list(self.time_series)[0]
        self.end_date = list(self.time_series)[-1]
        self.frequency = getattr(AllFrequencies, frequency)

    def __repr__(self):
        if len(self.time_series) > 6:
            printable_data_1 = list(self.time_series)[:3]
            printable_data_2 = list(self.time_series)[-3:]
            printable_str = "TimeSeries([{}\n\t...\n\t{}])".format(
                                ',\n\t'.join([str({i: self.time_series[i]}) for i in printable_data_1]),
                                ',\n\t'.join([str({i: self.time_series[i]}) for i in printable_data_2])
                                )
        else:
            printable_data = self.time_series
            printable_str = "TimeSeries([{}])".format(',\n\t'.join(
                                [str({i: self.time_series[i]}) for i in printable_data]))
        return printable_str

    def __str__(self):
        if len(self.time_series) > 6:
            printable_data_1 = list(self.time_series)[:3]
            printable_data_2 = list(self.time_series)[-3:]
            printable_str = "[{}\n ...\n {}]".format(
                                ',\n '.join([str({i: self.time_series[i]}) for i in printable_data_1]),
                                ',\n '.join([str({i: self.time_series[i]}) for i in printable_data_2])
                                )
        else:
            printable_data = self.time_series
            printable_str = "[{}]".format(',\n '.join([str({i: self.time_series[i]}) for i in printable_data]))
        return printable_str

    def __getitem__(self, n):
        keys = list(self.time_series.keys())
        key = keys[n]
        item = self.time_series[key]
        return key, item

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
        result = [item for item in self.time_series.items() if item[0] in keys]
        return result


class TimeSeries(TimeSeriesCore):
    """Container for TimeSeries objects"""

    def info(self):
        """Summary info about the TimeSeries object"""

        total_dates = len(self.time_series.keys())
        res_string = "First date: {}\nLast date: {}\nNumber of rows: {}"
        return res_string.format(self.start_date, self.end_date, total_dates)

    def ffill(self, inplace=False):
        num_days = (self.end_date - self.start_date).days + 1

        new_ts = dict()
        for i in range(num_days):
            cur_date = self.start_date + datetime.timedelta(days=i)
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
        as_on_match: str = 'closest',
        prior_match: str = 'closest',
        closest: str = "previous",
        compounding: bool = True,
        years: int = 1
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
        as_on_match: str = 'closest',
        prior_match: str = 'closest',
        closest: str = "previous",
        compounding: bool = True,
        years: int = 1,
    ) -> List[tuple]:
        """Calculates the rolling return"""

        all_dates = create_date_series(from_date, to_date, getattr(AllFrequencies, frequency))
        dates = set(all_dates)
        if frequency == AllFrequencies.D:
            dates = all_dates.intersection(self.dates)

        rolling_returns = []
        for i in dates:
            returns = self.calculate_returns(as_on=i, compounding=compounding, years=years, as_on_match=as_on_match,
                                             prior_match=prior_match, closest=closest)
            rolling_returns.append((i, returns))
        self.rolling_returns = rolling_returns
        return self.rolling_returns


if __name__ == '__main__':
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
