import datetime

from fincal.core import AllFrequencies, Frequency, Series
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
        series = Series([1, 2, 3, 4, 5, 6, 7], data_type=int)
        assert series.dtype == float
        assert series[2] == 3

        dates = create_date_series('2021-01-01', '2021-01-31', 'D')
        series = Series(dates, data_type=datetime.datetime)
        assert Series.dtype == datetime.datetime
