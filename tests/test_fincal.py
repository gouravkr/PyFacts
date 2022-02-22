import datetime
import os
import random
from typing import Literal, Sequence

import pytest
from fincal.core import Frequency, Series
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


class TestFincal:
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

    def test_ffill(self):
        data = create_test_data(frequency="D", eomonth=False, n=500, gaps=0.1, month_position="start", date_as_str=True)
        time_series = TimeSeries(data, frequency="D")
        ffill_data = time_series.ffill()
        assert len(ffill_data) >= 498

        ffill_data = time_series.ffill(inplace=True)
        assert ffill_data is None
        assert len(time_series) >= 498

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
