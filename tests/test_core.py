import datetime
from typing import Mapping

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
