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


class TimeSeries:
    """Container for TimeSeries objects"""

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
        self, as_on: datetime.datetime, closest: str = "previous", compounding: bool = True, years: int = 1
    ) -> float:
        """Method to calculate returns for a certain time-period as on a particular date
        >>> calculate_returns(datetime.date(2020, 1, 1), years=1)
        """

        try:
            current = self.time_series[as_on]
        except KeyError:
            raise ValueError("As on date not found")

        prev_date = as_on - relativedelta(years=years)
        if closest == "previous":
            delta = -1
        elif closest == "next":
            delta = 1
        else:
            raise ValueError(f"Invalid value for closest parameter: {closest}")

        while True:
            try:
                previous = self.time_series[prev_date]
                break
            except KeyError:
                prev_date = prev_date + relativedelta(days=delta)

        returns = current / previous
        if compounding:
            returns = returns ** (1 / years)
        return returns - 1

    def calculate_rolling_returns(
        self,
        from_date: datetime.date,
        to_date: datetime.date,
        frequency: str = "D",
        closest: str = "previous",
        compounding: bool = True,
        years: int = 1,
    ) -> List[tuple]:
        """Calculates the rolling return"""

        datediff = (to_date - from_date).days
        all_dates = set()
        for i in range(datediff):
            all_dates.add(from_date + datetime.timedelta(days=i))
        dates = all_dates.intersection(self.dates)

        rolling_returns = []
        for i in dates:
            returns = self.calculate_returns(as_on=i, compounding=compounding, years=years, closest=closest)
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
