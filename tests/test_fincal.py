import datetime
import os
import random
from typing import Literal, Sequence

import pytest
from fincal.core import FincalOptions, Frequency, Series
from fincal.fincal import TimeSeries, create_date_series

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sample_data_path = os.path.join(THIS_DIR, "data")


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


class TestDateSeries:
    def test_daily(self):
        start_date = datetime.datetime(2020, 1, 1)
        end_date = datetime.datetime(2020, 12, 31)
        d = create_date_series(start_date, end_date, frequency="D")
        assert len(d) == 366

        start_date = datetime.datetime(2017, 1, 1)
        end_date = datetime.datetime(2017, 12, 31)
        d = create_date_series(start_date, end_date, frequency="D")
        assert len(d) == 365

        with pytest.raises(ValueError):
            create_date_series(start_date, end_date, frequency="D", eomonth=True)

    def test_monthly(self):
        start_date = datetime.datetime(2020, 1, 1)
        end_date = datetime.datetime(2020, 12, 31)
        d = create_date_series(start_date, end_date, frequency="M")
        assert len(d) == 12

        d = create_date_series(start_date, end_date, frequency="M", eomonth=True)
        assert datetime.datetime(2020, 2, 29) in d

        start_date = datetime.datetime(2020, 1, 31)
        d = create_date_series(start_date, end_date, frequency="M")
        assert datetime.datetime(2020, 2, 29) in d
        assert datetime.datetime(2020, 8, 31) in d
        assert datetime.datetime(2020, 10, 30) not in d

        start_date = datetime.datetime(2020, 2, 29)
        d = create_date_series(start_date, end_date, frequency="M")
        assert len(d) == 11
        assert datetime.datetime(2020, 2, 29) in d
        assert datetime.datetime(2020, 8, 31) not in d
        assert datetime.datetime(2020, 10, 29) in d

    def test_quarterly(self):
        start_date = datetime.datetime(2018, 1, 1)
        end_date = datetime.datetime(2020, 12, 31)
        d = create_date_series(start_date, end_date, frequency="Q")
        assert len(d) == 12

        d = create_date_series(start_date, end_date, frequency="Q", eomonth=True)
        assert datetime.datetime(2020, 4, 30) in d

        start_date = datetime.datetime(2020, 1, 31)
        d = create_date_series(start_date, end_date, frequency="Q")
        assert len(d) == 4
        assert datetime.datetime(2020, 2, 29) not in d
        assert max(d) == datetime.datetime(2020, 10, 31)

        start_date = datetime.datetime(2020, 2, 29)
        d = create_date_series(start_date, end_date, frequency="Q")
        assert datetime.datetime(2020, 2, 29) in d
        assert datetime.datetime(2020, 8, 31) not in d
        assert datetime.datetime(2020, 11, 29) in d

        d = create_date_series(start_date, end_date, frequency="Q", eomonth=True)
        assert datetime.datetime(2020, 11, 30) in d


class TestFincalBasic:
    def test_creation(self):
        data = create_test_data(frequency="D", eomonth=False, n=50, gaps=0, month_position="start", date_as_str=True)
        time_series = TimeSeries(data, frequency="D")
        assert len(time_series) == 50
        assert isinstance(time_series.frequency, Frequency)
        assert time_series.frequency.days == 1

        ffill_data = time_series.ffill()
        assert len(ffill_data) == 50

        data = create_test_data(frequency="D", eomonth=False, n=500, gaps=0.1, month_position="start", date_as_str=True)
        time_series = TimeSeries(data, frequency="D")
        assert len(time_series) == 450

    def test_fill(self):
        data = create_test_data(frequency="D", eomonth=False, n=500, gaps=0.1, month_position="start", date_as_str=True)
        time_series = TimeSeries(data, frequency="D")
        ffill_data = time_series.ffill()
        assert len(ffill_data) >= 498

        ffill_data = time_series.ffill(inplace=True)
        assert ffill_data is None
        assert len(time_series) >= 498

        data = create_test_data(frequency="D", eomonth=False, n=500, gaps=0.1, month_position="start", date_as_str=True)
        time_series = TimeSeries(data, frequency="D")
        bfill_data = time_series.bfill()
        assert len(bfill_data) >= 498

        bfill_data = time_series.bfill(inplace=True)
        assert bfill_data is None
        assert len(time_series) >= 498

        data = [("2021-01-01", 220), ("2021-01-02", 230), ("2021-03-04", 240)]
        ts = TimeSeries(data, frequency="D")
        ff = ts.ffill()
        assert ff["2021-01-03"][1] == 230

        bf = ts.bfill()
        assert bf["2021-01-03"][1] == 240

    def test_iloc_slicing(self):
        data = create_test_data(frequency="D", eomonth=False, n=50, gaps=0, month_position="start", date_as_str=True)
        time_series = TimeSeries(data, frequency="D")
        assert time_series.iloc[0] is not None
        assert time_series.iloc[:3] is not None
        assert time_series.iloc[5:7] is not None
        assert isinstance(time_series.iloc[0], tuple)
        assert isinstance(time_series.iloc[10:20], list)
        assert len(time_series.iloc[10:20]) == 10

    def test_key_slicing(self):
        data = create_test_data(frequency="D", eomonth=False, n=50, gaps=0, month_position="start", date_as_str=True)
        time_series = TimeSeries(data, frequency="D")
        available_date = time_series.iloc[5][0]
        assert time_series[available_date] is not None
        assert isinstance(time_series["dates"], Series)
        assert isinstance(time_series["values"], Series)
        assert len(time_series.dates) == 50
        assert len(time_series.values) == 50


class TestReturns:
    data = [
            ('2020-01-01', 10),
            ('2020-02-01', 12),
            ('2020-03-01', 14),
            ('2020-04-01', 16),
            ('2020-05-01', 18),
            ('2020-06-01', 20),
            ('2020-07-01', 22),
            ('2020-08-01', 24),
            ('2020-09-01', 26),
            ('2020-10-01', 28),
            ('2020-11-01', 30),
            ('2020-12-01', 32),
            ('2021-01-01', 34)
        ]

    def test_returns_calc(self):
        ts = TimeSeries(self.data, frequency='M')
        returns = ts.calculate_returns("2021-01-01", compounding=False, interval_type='years', interval_value=1)
        assert returns == 2.4
        returns = ts.calculate_returns("2020-04-01", compounding=False, interval_type='months', interval_value=3)
        assert round(returns, 4) == 0.6
        returns = ts.calculate_returns("2020-04-01", compounding=True, interval_type='months', interval_value=3)
        assert round(returns, 4) == 5.5536
        returns = ts.calculate_returns("2020-04-01", compounding=False, interval_type='days', interval_value=90)
        assert round(returns, 4) == 0.6
        returns = ts.calculate_returns("2020-04-01", compounding=True, interval_type='days', interval_value=90)
        assert round(returns, 4) == 5.727
        returns = ts.calculate_returns("2020-04-10", compounding=True, interval_type='days', interval_value=90)
        assert round(returns, 4) == 5.727
        with pytest.raises(ValueError):
            ts.calculate_returns("2020-04-10", interval_type='days', interval_value=90, as_on_match='exact')

    def test_date_formats(self):
        ts = TimeSeries(self.data, frequency='M')
        FincalOptions.date_format = '%d-%m-%Y'
        with pytest.raises(ValueError):
            ts.calculate_returns("2020-04-10", compounding=True, interval_type='days', interval_value=90)

        returns1 = ts.calculate_returns("2020-04-10", interval_type='days', interval_value=90, date_format='%Y-%m-%d')
        returns2 = ts.calculate_returns("10-04-2020", interval_type='days', interval_value=90)
        assert round(returns1, 4) == round(returns2, 4) == 5.727

        FincalOptions.date_format = '%m-%d-%Y'
        with pytest.raises(ValueError):
            ts.calculate_returns("2020-04-10", compounding=True, interval_type='days', interval_value=90)

        returns1 = ts.calculate_returns("2020-04-10", interval_type='days', interval_value=90, date_format='%Y-%m-%d')
        returns2 = ts.calculate_returns("04-10-2020", interval_type='days', interval_value=90)
        assert round(returns1, 4) == round(returns2, 4) == 5.727
