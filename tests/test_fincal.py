import datetime

import pytest
from fincal import (
    AllFrequencies,
    FincalOptions,
    Frequency,
    TimeSeries,
    create_date_series,
)
from fincal.exceptions import DateNotFoundError


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


class TestTimeSeriesCreation:
    def test_creation_with_list_of_tuples(self, create_test_data):
        ts_data = create_test_data(frequency=AllFrequencies.D, num=50)
        ts = TimeSeries(ts_data, frequency="D")
        assert len(ts) == 50
        assert isinstance(ts.frequency, Frequency)
        assert ts.frequency.days == 1

    def test_creation_with_string_dates(self, create_test_data):
        ts_data = create_test_data(frequency=AllFrequencies.D, num=50)
        ts_data1 = [(dt.strftime("%Y-%m-%d"), val) for dt, val in ts_data]
        ts = TimeSeries(ts_data1, frequency="D")
        datetime.datetime(2017, 1, 1) in ts

        ts_data1 = [(dt.strftime("%d-%m-%Y"), val) for dt, val in ts_data]
        ts = TimeSeries(ts_data1, frequency="D", date_format="%d-%m-%Y")
        datetime.datetime(2017, 1, 1) in ts

        ts_data1 = [(dt.strftime("%m-%d-%Y"), val) for dt, val in ts_data]
        ts = TimeSeries(ts_data1, frequency="D", date_format="%m-%d-%Y")
        datetime.datetime(2017, 1, 1) in ts

        ts_data1 = [(dt.strftime("%m-%d-%Y %H:%M"), val) for dt, val in ts_data]
        ts = TimeSeries(ts_data1, frequency="D", date_format="%m-%d-%Y %H:%M")
        datetime.datetime(2017, 1, 1, 0, 0) in ts

    def test_creation_with_list_of_dicts(self, create_test_data):
        ts_data = create_test_data(frequency=AllFrequencies.D, num=50)
        ts_data1 = [{"date": dt.strftime("%Y-%m-%d"), "value": val} for dt, val in ts_data]
        ts = TimeSeries(ts_data1, frequency="D")
        datetime.datetime(2017, 1, 1) in ts

    def test_creation_with_list_of_lists(self, create_test_data):
        ts_data = create_test_data(frequency=AllFrequencies.D, num=50)
        ts_data1 = [[dt.strftime("%Y-%m-%d"), val] for dt, val in ts_data]
        ts = TimeSeries(ts_data1, frequency="D")
        datetime.datetime(2017, 1, 1) in ts

    def test_creation_with_dict(self, create_test_data):
        ts_data = create_test_data(frequency=AllFrequencies.D, num=50)
        ts_data1 = [{dt.strftime("%Y-%m-%d"): val} for dt, val in ts_data]
        ts = TimeSeries(ts_data1, frequency="D")
        datetime.datetime(2017, 1, 1) in ts


class TestTimeSeriesBasics:
    def test_fill(self, create_test_data):
        FincalOptions.get_closest = "exact"
        ts_data = create_test_data(frequency=AllFrequencies.D, num=50, skip_weekends=True)
        ts = TimeSeries(ts_data, frequency="D")
        ffill_data = ts.ffill()
        assert len(ffill_data) == 68

        ffill_data = ts.ffill(inplace=True)
        assert ffill_data is None
        assert len(ts) == 68

        ts_data = create_test_data(frequency=AllFrequencies.D, num=50, skip_weekends=True)
        ts = TimeSeries(ts_data, frequency="D")
        bfill_data = ts.bfill()
        assert len(bfill_data) == 68

        bfill_data = ts.bfill(inplace=True)
        assert bfill_data is None
        assert len(ts) == 68

        data = [("2021-01-01", 220), ("2021-01-02", 230), ("2021-01-04", 240)]
        ts = TimeSeries(data, frequency="D")
        ff = ts.ffill()
        assert ff["2021-01-03"][1] == 230

        bf = ts.bfill()
        assert bf["2021-01-03"][1] == 240

    def test_fill_weekly(self, create_test_data):
        ts_data = create_test_data(frequency=AllFrequencies.W, num=10)
        ts_data.pop(2)
        ts_data.pop(6)
        ts = TimeSeries(ts_data, frequency="W")
        assert len(ts) == 8

        ff = ts.ffill()
        assert len(ff) == 10
        assert "2017-01-15" in ff
        assert ff["2017-01-15"][1] == ff["2017-01-08"][1]

        bf = ts.bfill()
        assert len(ff) == 10
        assert "2017-01-15" in bf
        assert bf["2017-01-15"][1] == bf["2017-01-22"][1]

    def test_fill_monthly(self, create_test_data):
        ts_data = create_test_data(frequency=AllFrequencies.M, num=10)
        ts_data.pop(2)
        ts_data.pop(6)
        ts = TimeSeries(ts_data, frequency="M")
        assert len(ts) == 8

        ff = ts.ffill()
        assert len(ff) == 10
        assert "2017-03-01" in ff
        assert ff["2017-03-01"][1] == ff["2017-02-01"][1]

        bf = ts.bfill()
        assert len(bf) == 10
        assert "2017-08-01" in bf
        assert bf["2017-08-01"][1] == bf["2017-09-01"][1]

    def test_fill_eomonthly(self, create_test_data):
        ts_data = create_test_data(frequency=AllFrequencies.M, num=10, eomonth=True)
        ts_data.pop(2)
        ts_data.pop(6)
        ts = TimeSeries(ts_data, frequency="M")
        assert len(ts) == 8

        ff = ts.ffill()
        assert len(ff) == 10
        assert "2017-03-31" in ff
        assert ff["2017-03-31"][1] == ff["2017-02-28"][1]

        bf = ts.bfill()
        assert len(bf) == 10
        assert "2017-08-31" in bf
        assert bf["2017-08-31"][1] == bf["2017-09-30"][1]

    def test_fill_quarterly(self, create_test_data):
        ts_data = create_test_data(frequency=AllFrequencies.Q, num=10, eomonth=True)
        ts_data.pop(2)
        ts_data.pop(6)
        ts = TimeSeries(ts_data, frequency="Q")
        assert len(ts) == 8

        ff = ts.ffill()
        assert len(ff) == 10
        assert "2017-07-31" in ff
        assert ff["2017-07-31"][1] == ff["2017-04-30"][1]

        bf = ts.bfill()
        assert len(bf) == 10
        assert "2018-10-31" in bf
        assert bf["2018-10-31"][1] == bf["2019-01-31"][1]


class TestReturns:
    def test_returns_calc(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.D, skip_weekends=True)
        ts = TimeSeries(ts_data, "D")
        returns = ts.calculate_returns(
            "2020-01-01", annual_compounded_returns=False, return_period_unit="years", return_period_value=1
        )
        assert round(returns[1], 6) == 0.112913

        returns = ts.calculate_returns(
            "2020-04-01", annual_compounded_returns=False, return_period_unit="months", return_period_value=3
        )
        assert round(returns[1], 6) == 0.015908

        returns = ts.calculate_returns(
            "2020-04-01", annual_compounded_returns=True, return_period_unit="months", return_period_value=3
        )
        assert round(returns[1], 6) == 0.065167

        returns = ts.calculate_returns(
            "2020-04-01", annual_compounded_returns=False, return_period_unit="days", return_period_value=90
        )
        assert round(returns[1], 6) == 0.017673

        returns = ts.calculate_returns(
            "2020-04-01", annual_compounded_returns=True, return_period_unit="days", return_period_value=90
        )
        assert round(returns[1], 6) == 0.073632

        with pytest.raises(DateNotFoundError):
            ts.calculate_returns("2020-04-04", return_period_unit="days", return_period_value=90, as_on_match="exact")
        with pytest.raises(DateNotFoundError):
            ts.calculate_returns("2020-04-04", return_period_unit="months", return_period_value=3, prior_match="exact")

    def test_date_formats(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.D, skip_weekends=True)
        ts = TimeSeries(ts_data, "D")
        FincalOptions.date_format = "%d-%m-%Y"
        with pytest.raises(ValueError):
            ts.calculate_returns(
                "2020-04-10", annual_compounded_returns=True, return_period_unit="days", return_period_value=90
            )

        returns1 = ts.calculate_returns(
            "2020-04-01", return_period_unit="days", return_period_value=90, date_format="%Y-%m-%d"
        )
        returns2 = ts.calculate_returns("01-04-2020", return_period_unit="days", return_period_value=90)
        assert round(returns1[1], 6) == round(returns2[1], 6) == 0.073632

        FincalOptions.date_format = "%m-%d-%Y"
        with pytest.raises(ValueError):
            ts.calculate_returns(
                "2020-04-01", annual_compounded_returns=True, return_period_unit="days", return_period_value=90
            )

        returns1 = ts.calculate_returns(
            "2020-04-01", return_period_unit="days", return_period_value=90, date_format="%Y-%m-%d"
        )
        returns2 = ts.calculate_returns("04-01-2020", return_period_unit="days", return_period_value=90)
        assert round(returns1[1], 6) == round(returns2[1], 6) == 0.073632

    def test_limits(self, create_test_data):
        FincalOptions.date_format = "%Y-%m-%d"
        ts_data = create_test_data(AllFrequencies.D)
        ts = TimeSeries(ts_data, "D")
        with pytest.raises(DateNotFoundError):
            ts.calculate_returns("2020-11-25", return_period_unit="days", return_period_value=90, closest_max_days=10)

    def test_rolling_returns(self):
        # To-do
        return True


class TestExpand:
    def test_weekly_to_daily(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.W, num=10)
        ts = TimeSeries(ts_data, "W")
        expanded_ts = ts.expand("D", "ffill")
        assert len(expanded_ts) == 64
        assert expanded_ts.frequency.name == "daily"
        assert expanded_ts.iloc[0][1] == expanded_ts.iloc[1][1]

    def test_weekly_to_daily_no_weekends(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.W, num=10)
        ts = TimeSeries(ts_data, "W")
        expanded_ts = ts.expand("D", "ffill", skip_weekends=True)
        assert len(expanded_ts) == 46
        assert expanded_ts.frequency.name == "daily"
        assert expanded_ts.iloc[0][1] == expanded_ts.iloc[1][1]

    def test_monthly_to_daily(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.M, num=6)
        ts = TimeSeries(ts_data, "M")
        expanded_ts = ts.expand("D", "ffill")
        assert len(expanded_ts) == 152
        assert expanded_ts.frequency.name == "daily"
        assert expanded_ts.iloc[0][1] == expanded_ts.iloc[1][1]

    def test_monthly_to_daily_no_weekends(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.M, num=6)
        ts = TimeSeries(ts_data, "M")
        expanded_ts = ts.expand("D", "ffill", skip_weekends=True)
        assert len(expanded_ts) == 109
        assert expanded_ts.frequency.name == "daily"
        assert expanded_ts.iloc[0][1] == expanded_ts.iloc[1][1]

    def test_monthly_to_weekly(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.M, num=6)
        ts = TimeSeries(ts_data, "M")
        expanded_ts = ts.expand("W", "ffill")
        assert len(expanded_ts) == 22
        assert expanded_ts.frequency.name == "weekly"
        assert expanded_ts.iloc[0][1] == expanded_ts.iloc[1][1]

    def test_yearly_to_monthly(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.Y, num=5)
        ts = TimeSeries(ts_data, "Y")
        expanded_ts = ts.expand("M", "ffill")
        assert len(expanded_ts) == 49
        assert expanded_ts.frequency.name == "monthly"
        assert expanded_ts.iloc[0][1] == expanded_ts.iloc[1][1]


class TestShrink:
    # TODO
    pass


class TestMeanReturns:
    # TODO
    pass


class TestReadCsv:
    # TODO
    pass


class TestTransform:
    def test_daily_to_weekly(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.D, num=782, skip_weekends=True)
        ts = TimeSeries(ts_data, "D")
        tst = ts.transform("W", "mean")
        assert isinstance(tst, TimeSeries)
        assert len(tst) == 157
        assert "2017-01-30" in tst
        assert tst.iloc[4] == (datetime.datetime(2017, 1, 30), 1021.19)

    def test_daily_to_monthly(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.D, num=782, skip_weekends=False)
        ts = TimeSeries(ts_data, "D")
        tst = ts.transform("M", "mean")
        assert isinstance(tst, TimeSeries)
        assert len(tst) == 26
        assert "2018-01-01" in tst
        assert round(tst.iloc[12][1], 2) == 1146.1

    def test_daily_to_yearly(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.D, num=782, skip_weekends=True)
        ts = TimeSeries(ts_data, "D")
        tst = ts.transform("Y", "mean")
        assert isinstance(tst, TimeSeries)
        assert len(tst) == 3
        assert "2019-01-02" in tst
        assert tst.iloc[2] == (datetime.datetime(2019, 1, 2), 1238.5195)

    def test_weekly_to_monthly(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.W, num=261)
        ts = TimeSeries(ts_data, "W")
        tst = ts.transform("M", "mean")
        assert isinstance(tst, TimeSeries)
        assert "2017-01-01" in tst
        assert tst.iloc[0] == (datetime.datetime(2017, 1, 1), 1007.33)

    def test_weekly_to_qty(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.W, num=261)
        ts = TimeSeries(ts_data, "W")
        tst = ts.transform("Q", "mean")
        assert len(tst) == 20
        assert "2018-01-01" in tst
        assert round(tst.iloc[4][1], 2) == 1054.72

    def test_weekly_to_yearly(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.W, num=261)
        ts = TimeSeries(ts_data, "W")
        tst = ts.transform("Y", "mean")
        assert "2019-01-01" in tst
        assert round(tst.iloc[2][1], 2) == 1054.50
        with pytest.raises(ValueError):
            ts.transform("D", "mean")

    def test_monthly_to_qty(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.M, num=36)
        ts = TimeSeries(ts_data, "M")
        tst = ts.transform("Q", "mean")
        assert len(tst) == 12
        assert "2018-10-01" in tst
        assert tst.iloc[7] == (datetime.datetime(2018, 10, 1), 1021.19)
        with pytest.raises(ValueError):
            ts.transform("M", "sum")


class TestReturnsAgain:
    data = [
        ("2020-01-01", 10),
        ("2020-02-01", 12),
        ("2020-03-01", 14),
        ("2020-04-01", 16),
        ("2020-05-01", 18),
        ("2020-06-01", 20),
        ("2020-07-01", 22),
        ("2020-08-01", 24),
        ("2020-09-01", 26),
        ("2020-10-01", 28),
        ("2020-11-01", 30),
        ("2020-12-01", 32),
        ("2021-01-01", 34),
    ]

    def test_returns_calc(self):
        ts = TimeSeries(self.data, frequency="M")
        returns = ts.calculate_returns(
            "2021-01-01", annual_compounded_returns=False, return_period_unit="years", return_period_value=1
        )
        assert returns[1] == 2.4
        returns = ts.calculate_returns(
            "2020-04-01", annual_compounded_returns=False, return_period_unit="months", return_period_value=3
        )
        assert round(returns[1], 4) == 0.6
        returns = ts.calculate_returns(
            "2020-04-01", annual_compounded_returns=True, return_period_unit="months", return_period_value=3
        )
        assert round(returns[1], 4) == 5.5536
        returns = ts.calculate_returns(
            "2020-04-01", annual_compounded_returns=False, return_period_unit="days", return_period_value=90
        )
        assert round(returns[1], 4) == 0.6
        returns = ts.calculate_returns(
            "2020-04-01", annual_compounded_returns=True, return_period_unit="days", return_period_value=90
        )
        assert round(returns[1], 4) == 5.727
        returns = ts.calculate_returns(
            "2020-04-10", annual_compounded_returns=True, return_period_unit="days", return_period_value=90
        )
        assert round(returns[1], 4) == 5.727
        with pytest.raises(DateNotFoundError):
            ts.calculate_returns("2020-04-10", return_period_unit="days", return_period_value=90, as_on_match="exact")
        with pytest.raises(DateNotFoundError):
            ts.calculate_returns("2020-04-10", return_period_unit="days", return_period_value=90, prior_match="exact")

    def test_date_formats(self):
        ts = TimeSeries(self.data, frequency="M")
        FincalOptions.date_format = "%d-%m-%Y"
        with pytest.raises(ValueError):
            ts.calculate_returns(
                "2020-04-10", annual_compounded_returns=True, return_period_unit="days", return_period_value=90
            )

        returns1 = ts.calculate_returns(
            "2020-04-10", return_period_unit="days", return_period_value=90, date_format="%Y-%m-%d"
        )
        returns2 = ts.calculate_returns("10-04-2020", return_period_unit="days", return_period_value=90)
        assert round(returns1[1], 4) == round(returns2[1], 4) == 5.727

        FincalOptions.date_format = "%m-%d-%Y"
        with pytest.raises(ValueError):
            ts.calculate_returns(
                "2020-04-10", annual_compounded_returns=True, return_period_unit="days", return_period_value=90
            )

        returns1 = ts.calculate_returns(
            "2020-04-10", return_period_unit="days", return_period_value=90, date_format="%Y-%m-%d"
        )
        returns2 = ts.calculate_returns("04-10-2020", return_period_unit="days", return_period_value=90)
        assert round(returns1[1], 4) == round(returns2[1], 4) == 5.727

    def test_limits(self):
        ts = TimeSeries(self.data, frequency="M")
        FincalOptions.date_format = "%Y-%m-%d"
        with pytest.raises(DateNotFoundError):
            ts.calculate_returns("2020-04-25", return_period_unit="days", return_period_value=90, closest_max_days=10)


class TestVolatility:
    def test_daily_ts(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.D)
        ts = TimeSeries(ts_data, "D")
        assert len(ts) == 1000
        sd = ts.volatility(annualize_volatility=False)
        assert round(sd, 6) == 0.002622
        sd = ts.volatility()
        assert round(sd, 6) == 0.050098
        sd = ts.volatility(annual_compounded_returns=True)
        assert round(sd, 4) == 37.9329
        sd = ts.volatility(return_period_unit="months", annual_compounded_returns=True)
        assert round(sd, 4) == 0.6778
        sd = ts.volatility(return_period_unit="years")
        assert round(sd, 6) == 0.023164
        sd = ts.volatility(from_date="2017-10-01", to_date="2019-08-31", annualize_volatility=True)
        assert round(sd, 6) == 0.050559
        sd = ts.volatility(from_date="2017-02-01", frequency="M", return_period_unit="months")
        assert round(sd, 6) == 0.050884
        sd = ts.volatility(
            frequency="M",
            return_period_unit="months",
            return_period_value=3,
            annualize_volatility=False,
        )
        assert round(sd, 6) == 0.020547


class TestDrawdown:
    def test_daily_ts(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.D, skip_weekends=True)
        ts = TimeSeries(ts_data, "D")
        mdd = ts.max_drawdown()
        assert isinstance(mdd, dict)
        assert len(mdd) == 3
        assert all(i in mdd for i in ["start_date", "end_date", "drawdown"])
        expeced_response = {
            "start_date": datetime.datetime(2017, 6, 6, 0, 0),
            "end_date": datetime.datetime(2017, 7, 31, 0, 0),
            "drawdown": -0.028293686030751997,
        }
        assert mdd == expeced_response

    def test_weekly_ts(self, create_test_data):
        ts_data = create_test_data(AllFrequencies.W, mu=1, sigma=0.5)
        ts = TimeSeries(ts_data, "W")
        mdd = ts.max_drawdown()
        assert isinstance(mdd, dict)
        assert len(mdd) == 3
        assert all(i in mdd for i in ["start_date", "end_date", "drawdown"])
        expeced_response = {
            "start_date": datetime.datetime(2019, 2, 17, 0, 0),
            "end_date": datetime.datetime(2019, 11, 17, 0, 0),
            "drawdown": -0.2584760499552089,
        }
        assert mdd == expeced_response


class TestSync:
    def test_weekly_to_daily(self, create_test_data):
        daily_data = create_test_data(AllFrequencies.D, num=15)
        weekly_data = create_test_data(AllFrequencies.W, num=3)

        daily_ts = TimeSeries(daily_data, frequency="D")
        weekly_ts = TimeSeries(weekly_data, frequency="W")

        synced_weekly_ts = daily_ts.sync(weekly_ts)
        assert len(daily_ts) == len(synced_weekly_ts)
        assert synced_weekly_ts.frequency == AllFrequencies.D
        assert "2017-01-02" in synced_weekly_ts
        assert synced_weekly_ts["2017-01-02"][1] == synced_weekly_ts["2017-01-01"][1]
