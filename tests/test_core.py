import datetime
import random
from typing import Literal, Mapping, Sequence

from fincal.core import AllFrequencies, Frequency, Series, TimeSeriesCore
from fincal.fincal import create_date_series


class TestFrequency:
    def test_creation(self):
        D = Frequency('daily', 'days', 1, 1, 'D')
        assert D.days == 1
        assert D.symbol == 'D'
        assert D.name == 'daily'
        assert D.value == 1
        assert D.freq_type == 'days'


def create_test_data(
    frequency: str,
    eomonth: bool,
    n: int,
    gaps: float,
    month_position: Literal["start", "middle", "end"],
    date_as_str: bool,
    as_outer_type: Literal["dict", "list"] = "list",
    as_inner_type: Literal["dict", "list", "tuple"] = "tuple",
) -> Sequence[tuple]:
    start_dates = {
        "start": datetime.datetime(2016, 1, 1),
        "middle": datetime.datetime(2016, 1, 15),
        "end": datetime.datetime(2016, 1, 31),
    }
    end_date = datetime.datetime(2021, 12, 31)
    dates = create_date_series(start_dates[month_position], end_date, frequency=frequency, eomonth=eomonth)
    dates = dates[:n]
    if gaps:
        num_gaps = int(len(dates) * gaps)
        to_remove = random.sample(dates, num_gaps)
        for i in to_remove:
            dates.remove(i)
    if date_as_str:
        dates = [i.strftime("%Y-%m-%d") for i in dates]

    values = [random.randint(8000, 90000) / 100 for _ in dates]

    data = list(zip(dates, values))
    if as_outer_type == "list":
        if as_inner_type == "list":
            data = [list(i) for i in data]
        elif as_inner_type == "dict[1]":
            data = [dict((i,)) for i in data]
        elif as_inner_type == "dict[2]":
            data = [dict(date=i, value=j) for i, j in data]
    elif as_outer_type == "dict":
        data = dict(data)

    return data


class TestAllFrequencies:
    def test_attributes(self):
        assert hasattr(AllFrequencies, 'D')
        assert hasattr(AllFrequencies, 'M')
        assert hasattr(AllFrequencies, 'Q')

    def test_days(self):
        assert AllFrequencies.D.days == 1
        assert AllFrequencies.M.days == 30
        assert AllFrequencies.Q.days == 91

    def test_symbol(self):
        assert AllFrequencies.H.symbol == 'H'
        assert AllFrequencies.W.symbol == 'W'

    def test_values(self):
        assert AllFrequencies.H.value == 6
        assert AllFrequencies.Y.value == 1

    def test_type(self):
        assert AllFrequencies.Q.freq_type == 'months'
        assert AllFrequencies.W.freq_type == 'days'


class TestSeries:
    def test_creation(self):
        series = Series([1, 2, 3, 4, 5, 6, 7], data_type='number')
        assert series.dtype == float
        assert series[2] == 3

        dates = create_date_series('2021-01-01', '2021-01-31', frequency='D')
        series = Series(dates, data_type='date')
        assert series.dtype == datetime.datetime


class TestTimeSeriesCore:
    data = [('2021-01-01', 220), ('2021-02-01', 230), ('2021-03-01', 240)]

    def test_repr_str(self):
        ts = TimeSeriesCore(self.data, frequency='M')
        assert str(ts) in repr(ts).replace('\t', ' ')

        data = create_test_data(frequency="D", eomonth=False, n=50, gaps=0, month_position="start", date_as_str=True)
        ts = TimeSeriesCore(data, frequency="D")
        assert '...' in str(ts)
        assert '...' in repr(ts)

    def test_creation(self):
        ts = TimeSeriesCore(self.data, frequency='M')
        assert isinstance(ts, TimeSeriesCore)
        assert isinstance(ts, Mapping)

    def test_getitem(self):
        ts = TimeSeriesCore(self.data, frequency='M')
        assert ts.dates[0] == datetime.datetime(2021, 1, 1, 0, 0)
        assert ts.values[0] == 220
        assert ts['2021-01-01'][1] == 220
        assert len(ts[ts.dates > '2021-01-01']) == 2
        assert ts[ts.dates == '2021-02-01'].iloc[0][1] == 230
        assert ts.iloc[2][0] == datetime.datetime(2021, 3, 1)
        assert len(ts.iloc[:2]) == 2

    def test_contains(self):
        ts = TimeSeriesCore(self.data, frequency='M')
        assert datetime.datetime(2021, 1, 1) in ts
        assert '2021-01-01' in ts
        assert '2021-01-14' not in ts

    def test_items(self):
        ts = TimeSeriesCore(self.data, frequency='M')
        for i, j in ts.items():
            assert j == self.data[0][1]
            break
