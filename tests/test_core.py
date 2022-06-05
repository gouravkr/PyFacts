import datetime
import random
from typing import Literal, Mapping, Sequence

import pytest
from pyfacts.core import AllFrequencies, Frequency, Series, TimeSeriesCore
from pyfacts.pyfacts import create_date_series
from pyfacts.utils import PyfactsOptions


class TestFrequency:
    def test_creation(self):
        D = Frequency("daily", "days", 1, 1, "D")
        assert D.days == 1
        assert D.symbol == "D"
        assert D.name == "daily"
        assert D.value == 1
        assert D.freq_type == "days"


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
        assert hasattr(AllFrequencies, "D")
        assert hasattr(AllFrequencies, "M")
        assert hasattr(AllFrequencies, "Q")

    def test_days(self):
        assert AllFrequencies.D.days == 1
        assert AllFrequencies.M.days == 30
        assert AllFrequencies.Q.days == 91

    def test_symbol(self):
        assert AllFrequencies.H.symbol == "H"
        assert AllFrequencies.W.symbol == "W"

    def test_values(self):
        assert AllFrequencies.H.value == 6
        assert AllFrequencies.Y.value == 1

    def test_type(self):
        assert AllFrequencies.Q.freq_type == "months"
        assert AllFrequencies.W.freq_type == "days"


class TestSeries:
    def test_creation(self):
        series = Series([1, 2, 3, 4, 5, 6, 7], dtype="number")
        assert series.dtype == float
        assert series[2] == 3

        dates = create_date_series("2021-01-01", "2021-01-31", frequency="D")
        series = Series(dates, dtype="date")
        assert series.dtype == datetime.datetime


class TestTimeSeriesCore:
    data = [("2021-01-01", 220), ("2021-02-01", 230), ("2021-03-01", 240)]

    def test_repr_str(self):
        ts = TimeSeriesCore(self.data, frequency="M")
        assert str(ts) in repr(ts).replace("\t", " ")

        data = create_test_data(frequency="D", eomonth=False, n=50, gaps=0, month_position="start", date_as_str=True)
        ts = TimeSeriesCore(data, frequency="D")
        assert "..." in str(ts)
        assert "..." in repr(ts)

    def test_creation(self):
        ts = TimeSeriesCore(self.data, frequency="M")
        assert isinstance(ts, TimeSeriesCore)
        assert isinstance(ts, Mapping)


class TestSlicing:
    data = [("2021-01-01", 220), ("2021-02-01", 230), ("2021-03-01", 240)]

    def test_getitem(self):
        ts = TimeSeriesCore(self.data, frequency="M")
        assert ts.dates[0] == datetime.datetime(2021, 1, 1, 0, 0)
        assert ts.values[0] == 220
        assert ts["2021-01-01"][1] == 220
        assert len(ts[ts.dates > "2021-01-01"]) == 2
        assert ts[ts.dates == "2021-02-01"].iloc[0][1] == 230
        assert ts.iloc[2][0] == datetime.datetime(2021, 3, 1)
        assert len(ts.iloc[:2]) == 2
        with pytest.raises(KeyError):
            ts["2021-02-03"]
        subset_ts = ts[["2021-01-01", "2021-03-01"]]
        assert len(subset_ts) == 2
        assert isinstance(subset_ts, TimeSeriesCore)
        assert subset_ts.iloc[1][1] == 240

    def test_get(self):
        ts = TimeSeriesCore(self.data, frequency="M")
        assert ts.dates[0] == datetime.datetime(2021, 1, 1, 0, 0)
        assert ts.values[0] == 220
        assert ts.get("2021-01-01")[1] == 220
        assert ts.get("2021-02-15") is None
        assert ts.get("2021-02-23", -1) == -1
        assert ts.get("2021-02-10", closest="previous")[1] == 230
        assert ts.get("2021-02-10", closest="next")[1] == 240
        PyfactsOptions.get_closest = "previous"
        assert ts.get("2021-02-10")[1] == 230
        PyfactsOptions.get_closest = "next"
        assert ts.get("2021-02-10")[1] == 240

    def test_contains(self):
        ts = TimeSeriesCore(self.data, frequency="M")
        assert datetime.datetime(2021, 1, 1) in ts
        assert "2021-01-01" in ts
        assert "2021-01-14" not in ts

    def test_items(self):
        ts = TimeSeriesCore(self.data, frequency="M")
        for i, j in ts.items():
            assert j == self.data[0][1]
            break

    def test_special_keys(self):
        ts = TimeSeriesCore(self.data, frequency="M")
        dates = ts["dates"]
        values = ts["values"]
        assert isinstance(dates, Series)
        assert isinstance(values, Series)
        assert len(dates) == 3
        assert len(values) == 3
        assert dates[0] == datetime.datetime(2021, 1, 1, 0, 0)
        assert values[0] == 220

    def test_iloc_slicing(self):
        ts = TimeSeriesCore(self.data, frequency="M")
        assert ts.iloc[0] == (datetime.datetime(2021, 1, 1), 220)
        assert ts.iloc[-1] == (datetime.datetime(2021, 3, 1), 240)

        ts_slice = ts.iloc[0:2]
        assert isinstance(ts_slice, TimeSeriesCore)
        assert len(ts_slice) == 2


class TestSetitem:
    data = [("2021-01-01", 220), ("2021-01-04", 230), ("2021-03-07", 240)]

    def test_setitem(self):
        ts = TimeSeriesCore(self.data, frequency="M")
        assert len(ts) == 3

        ts["2021-01-02"] = 225
        assert len(ts) == 4
        assert ts["2021-01-02"][1] == 225

        ts["2021-01-02"] = 227.6
        assert len(ts) == 4
        assert ts["2021-01-02"][1] == 227.6

    def test_errors(self):
        ts = TimeSeriesCore(self.data, frequency="M")
        with pytest.raises(TypeError):
            ts["2021-01-03"] = "abc"

        with pytest.raises(NotImplementedError):
            ts.iloc[4] = 4

        with pytest.raises(ValueError):
            ts["abc"] = 12


class TestTimeSeriesCoreHeadTail:
    data = [
        ("2021-01-01", 220),
        ("2021-02-01", 230),
        ("2021-03-01", 240),
        ("2021-04-01", 250),
        ("2021-05-01", 260),
        ("2021-06-01", 270),
        ("2021-07-01", 280),
        ("2021-08-01", 290),
        ("2021-09-01", 300),
        ("2021-10-01", 310),
        ("2021-11-01", 320),
        ("2021-12-01", 330),
    ]

    def test_head(self):
        ts = TimeSeriesCore(self.data, frequency="M")
        assert len(ts.head()) == 6
        assert len(ts.head(3)) == 3
        assert isinstance(ts.head(), TimeSeriesCore)
        head_ts = ts.head(6)
        assert head_ts.iloc[-1][1] == 270

    def test_tail(self):
        ts = TimeSeriesCore(self.data, frequency="M")
        assert len(ts.tail()) == 6
        assert len(ts.tail(8)) == 8
        assert isinstance(ts.tail(), TimeSeriesCore)
        tail_ts = ts.tail(6)
        assert tail_ts.iloc[0][1] == 280

    def test_head_tail(self):
        ts = TimeSeriesCore(self.data, frequency="M")
        head_tail_ts = ts.head(8).tail(2)
        assert isinstance(head_tail_ts, TimeSeriesCore)
        assert "2021-07-01" in head_tail_ts
        assert head_tail_ts.iloc[1][1] == 290


class TestDelitem:
    data = [
        ("2021-01-01", 220),
        ("2021-02-01", 230),
        ("2021-03-01", 240),
        ("2021-04-01", 250),
    ]

    def test_deletion(self):
        ts = TimeSeriesCore(self.data, "M")
        assert len(ts) == 4
        del ts["2021-03-01"]
        assert len(ts) == 3
        assert "2021-03-01" not in ts

        with pytest.raises(KeyError):
            del ts["2021-03-01"]


class TestTimeSeriesComparisons:
    data1 = [
        ("2021-01-01", 220),
        ("2021-02-01", 230),
        ("2021-03-01", 240),
        ("2021-04-01", 250),
    ]

    data2 = [
        ("2021-01-01", 240),
        ("2021-02-01", 210),
        ("2021-03-01", 240),
        ("2021-04-01", 270),
    ]

    def test_number_comparison(self):
        ts1 = TimeSeriesCore(self.data1, "M")
        assert isinstance(ts1 > 23, TimeSeriesCore)
        assert (ts1 > 230).values == Series([0.0, 0.0, 1.0, 1.0], "float")
        assert (ts1 >= 230).values == Series([0.0, 1.0, 1.0, 1.0], "float")
        assert (ts1 < 240).values == Series([1.0, 1.0, 0.0, 0.0], "float")
        assert (ts1 <= 240).values == Series([1.0, 1.0, 1.0, 0.0], "float")
        assert (ts1 == 240).values == Series([0.0, 0.0, 1.0, 0.0], "float")
        assert (ts1 != 240).values == Series([1.0, 1.0, 0.0, 1.0], "float")

    def test_series_comparison(self):
        ts1 = TimeSeriesCore(self.data1, "M")
        ser = Series([240, 210, 240, 270], dtype="int")

        assert (ts1 > ser).values == Series([0.0, 1.0, 0.0, 0.0], "float")
        assert (ts1 >= ser).values == Series([0.0, 1.0, 1.0, 0.0], "float")
        assert (ts1 < ser).values == Series([1.0, 0.0, 0.0, 1.0], "float")
        assert (ts1 <= ser).values == Series([1.0, 0.0, 1.0, 1.0], "float")
        assert (ts1 == ser).values == Series([0.0, 0.0, 1.0, 0.0], "float")
        assert (ts1 != ser).values == Series([1.0, 1.0, 0.0, 1.0], "float")

    def test_tsc_comparison(self):
        ts1 = TimeSeriesCore(self.data1, "M")
        ts2 = TimeSeriesCore(self.data2, "M")

        assert (ts1 > ts2).values == Series([0.0, 1.0, 0.0, 0.0], "float")
        assert (ts1 >= ts2).values == Series([0.0, 1.0, 1.0, 0.0], "float")
        assert (ts1 < ts2).values == Series([1.0, 0.0, 0.0, 1.0], "float")
        assert (ts1 <= ts2).values == Series([1.0, 0.0, 1.0, 1.0], "float")
        assert (ts1 == ts2).values == Series([0.0, 0.0, 1.0, 0.0], "float")
        assert (ts1 != ts2).values == Series([1.0, 1.0, 0.0, 1.0], "float")

    def test_errors(self):
        ts1 = TimeSeriesCore(self.data1, "M")
        ts2 = TimeSeriesCore(self.data2, "M")
        ser = Series([240, 210, 240], dtype="int")
        ser2 = Series(["2021-01-01", "2021-02-01", "2021-03-01", "2021-04-01"], dtype="date")

        del ts2["2021-04-01"]

        with pytest.raises(TypeError):
            ts1 == "a"

        with pytest.raises(ValueError):
            ts1 > ts2

        with pytest.raises(TypeError):
            ts1 == ser2

        with pytest.raises(ValueError):
            ts1 <= ser

        with pytest.raises(TypeError):
            ts2 < [23, 24, 25, 26]


class TestTimeSeriesArithmatic:
    data = [
        ("2021-01-01", 220),
        ("2021-02-01", 230),
        ("2021-03-01", 240),
        ("2021-04-01", 250),
    ]

    def test_add(self):
        ts = TimeSeriesCore(self.data, "M")
        ser = ts.values

        num_add_ts = ts + 40
        assert num_add_ts["2021-01-01"][1] == 260
        assert num_add_ts["2021-04-01"][1] == 290

        num_radd_ts = 40 + ts
        assert num_radd_ts["2021-01-01"][1] == 260
        assert num_radd_ts["2021-04-01"][1] == 290

        ser_add_ts = ts + ser
        assert ser_add_ts["2021-01-01"][1] == 440
        assert ser_add_ts["2021-04-01"][1] == 500

        ts_add_ts = ts + num_add_ts
        assert ts_add_ts["2021-01-01"][1] == 480
        assert ts_add_ts["2021-04-01"][1] == 540

    def test_sub(self):
        ts = TimeSeriesCore(self.data, "M")
        ser = Series([20, 30, 40, 50], "number")

        num_sub_ts = ts - 40
        assert num_sub_ts["2021-01-01"][1] == 180
        assert num_sub_ts["2021-04-01"][1] == 210

        num_rsub_ts = 240 - ts
        assert num_rsub_ts["2021-01-01"][1] == 20
        assert num_rsub_ts["2021-04-01"][1] == -10

        ser_sub_ts = ts - ser
        assert ser_sub_ts["2021-01-01"][1] == 200
        assert ser_sub_ts["2021-04-01"][1] == 200

        ts_sub_ts = ts - num_sub_ts
        assert ts_sub_ts["2021-01-01"][1] == 40
        assert ts_sub_ts["2021-04-01"][1] == 40

    def test_truediv(self):
        ts = TimeSeriesCore(self.data, "M")
        ser = Series([22, 23, 24, 25], "number")

        num_div_ts = ts / 10
        assert num_div_ts["2021-01-01"][1] == 22
        assert num_div_ts["2021-04-01"][1] == 25

        num_rdiv_ts = 1000 / ts
        assert num_rdiv_ts["2021-04-01"][1] == 4

        ser_div_ts = ts / ser
        assert ser_div_ts["2021-01-01"][1] == 10
        assert ser_div_ts["2021-04-01"][1] == 10

        ts_div_ts = ts / num_div_ts
        assert ts_div_ts["2021-01-01"][1] == 10
        assert ts_div_ts["2021-04-01"][1] == 10

    def test_floordiv(self):
        ts = TimeSeriesCore(self.data, "M")
        ser = Series([22, 23, 24, 25], "number")

        num_div_ts = ts // 11
        assert num_div_ts["2021-02-01"][1] == 20
        assert num_div_ts["2021-04-01"][1] == 22

        num_rdiv_ts = 1000 // ts
        assert num_rdiv_ts["2021-01-01"][1] == 4

        ser_div_ts = ts // ser
        assert ser_div_ts["2021-01-01"][1] == 10
        assert ser_div_ts["2021-04-01"][1] == 10
