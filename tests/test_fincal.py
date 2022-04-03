import datetime
import math
import random
from typing import List

import pytest
from dateutil.relativedelta import relativedelta
from fincal.core import AllFrequencies, Frequency
from fincal.exceptions import DateNotFoundError
from fincal.fincal import TimeSeries, create_date_series
from fincal.utils import FincalOptions


def create_prices(s0: float, mu: float, sigma: float, num_prices: int) -> list:
    """Generates a price following a geometric brownian motion process based on the input of the arguments.

        Since this function is used only to generate data for tests, the seed is fixed as 1234.
        Many of the tests rely on exact values generated using this seed.
        If the seed is changed, those tests will fail.

    Parameters:
    ------------
    s0: float
        Asset inital price.

    mu: float
        Interest rate expressed annual terms.

    sigma: float
        Volatility expressed annual terms.

    num_prices: int
        number of prices to generate

    Returns:
    --------
        Returns a list of values generated using GBM algorithm
    """

    random.seed(1234)  # WARNING! Changing the seed will cause most tests to fail
    all_values = []
    for _ in range(num_prices):
        s0 *= math.exp(
            (mu - 0.5 * sigma**2) * (1.0 / 365.0) + sigma * math.sqrt(1.0 / 365.0) * random.gauss(mu=0, sigma=1)
        )
        all_values.append(round(s0, 2))

    return all_values


def create_test_data(
    frequency: Frequency,
    num: int = 1000,
    skip_weekends: bool = False,
    mu: float = 0.1,
    sigma: float = 0.05,
    eomonth: bool = False,
) -> List[tuple]:
    """Creates TimeSeries data

    Parameters:
    -----------
    frequency: Frequency
        The frequency of the time series data to be generated.

    num: int
        Number of date: value pairs to be generated.

    skip_weekends: bool
        Whether weekends (saturday, sunday) should be skipped.
        Gets used only if the frequency is daily.

    mu: float
        Mean return for the values.

    sigma: float
        standard deviation of the values.

    Returns:
    --------
        Returns a TimeSeries object
    """

    start_date = datetime.datetime(2017, 1, 1)
    timedelta_dict = {
        frequency.freq_type: int(
            frequency.value * num * (7 / 5 if frequency == AllFrequencies.D and skip_weekends else 1)
        )
    }
    end_date = start_date + relativedelta(**timedelta_dict)
    dates = create_date_series(start_date, end_date, frequency.symbol, skip_weekends=skip_weekends, eomonth=eomonth)
    values = create_prices(1000, mu, sigma, num)
    ts = list(zip(dates, values))
    return ts


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
    def test_creation_with_list_of_tuples(self):
        ts_data = create_test_data(frequency=AllFrequencies.D, num=50)
        ts = TimeSeries(ts_data, frequency="D")
        assert len(ts) == 50
        assert isinstance(ts.frequency, Frequency)
        assert ts.frequency.days == 1

    def test_creation_with_string_dates(self):
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

    def test_creation_with_list_of_dicts(self):
        ts_data = create_test_data(frequency=AllFrequencies.D, num=50)
        ts_data1 = [{"date": dt.strftime("%Y-%m-%d"), "value": val} for dt, val in ts_data]
        ts = TimeSeries(ts_data1, frequency="D")
        datetime.datetime(2017, 1, 1) in ts

    def test_creation_with_list_of_lists(self):
        ts_data = create_test_data(frequency=AllFrequencies.D, num=50)
        ts_data1 = [[dt.strftime("%Y-%m-%d"), val] for dt, val in ts_data]
        ts = TimeSeries(ts_data1, frequency="D")
        datetime.datetime(2017, 1, 1) in ts

    def test_creation_with_dict(self):
        ts_data = create_test_data(frequency=AllFrequencies.D, num=50)
        ts_data1 = [{dt.strftime("%Y-%m-%d"): val} for dt, val in ts_data]
        ts = TimeSeries(ts_data1, frequency="D")
        datetime.datetime(2017, 1, 1) in ts


class TestTimeSeriesBasics:
    def test_fill(self):
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

        data = [("2021-01-01", 220), ("2021-01-02", 230), ("2021-03-04", 240)]
        ts = TimeSeries(data, frequency="D")
        ff = ts.ffill()
        assert ff["2021-01-03"][1] == 230

        bf = ts.bfill()
        assert bf["2021-01-03"][1] == 240


class TestReturns:
    def test_returns_calc(self):
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

    def test_date_formats(self):
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

    def test_limits(self):
        FincalOptions.date_format = "%Y-%m-%d"
        ts_data = create_test_data(AllFrequencies.D)
        ts = TimeSeries(ts_data, "D")
        with pytest.raises(DateNotFoundError):
            ts.calculate_returns("2020-11-25", return_period_unit="days", return_period_value=90, closest_max_days=10)

    def test_rolling_returns(self):
        # Yet to be written
        return True


class TestExpand:
    def test_weekly_to_daily(self):
        ts_data = create_test_data(AllFrequencies.W, 10)
        ts = TimeSeries(ts_data, "W")
        expanded_ts = ts.expand("D", "ffill")
        assert len(expanded_ts) == 64
        assert expanded_ts.frequency.name == "daily"
        assert expanded_ts.iloc[0][1] == expanded_ts.iloc[1][1]

    def test_weekly_to_daily_no_weekends(self):
        ts_data = create_test_data(AllFrequencies.W, 10)
        ts = TimeSeries(ts_data, "W")
        expanded_ts = ts.expand("D", "ffill", skip_weekends=True)
        assert len(expanded_ts) == 45
        assert expanded_ts.frequency.name == "daily"
        assert expanded_ts.iloc[0][1] == expanded_ts.iloc[1][1]

    def test_monthly_to_daily(self):
        ts_data = create_test_data(AllFrequencies.M, 6)
        ts = TimeSeries(ts_data, "M")
        expanded_ts = ts.expand("D", "ffill")
        assert len(expanded_ts) == 152
        assert expanded_ts.frequency.name == "daily"
        assert expanded_ts.iloc[0][1] == expanded_ts.iloc[1][1]

    def test_monthly_to_daily_no_weekends(self):
        ts_data = create_test_data(AllFrequencies.M, 6)
        ts = TimeSeries(ts_data, "M")
        expanded_ts = ts.expand("D", "ffill", skip_weekends=True)
        assert len(expanded_ts) == 109
        assert expanded_ts.frequency.name == "daily"
        assert expanded_ts.iloc[0][1] == expanded_ts.iloc[1][1]

    def test_monthly_to_weekly(self):
        ts_data = create_test_data(AllFrequencies.M, 6)
        ts = TimeSeries(ts_data, "M")
        expanded_ts = ts.expand("W", "ffill")
        assert len(expanded_ts) == 22
        assert expanded_ts.frequency.name == "weekly"
        assert expanded_ts.iloc[0][1] == expanded_ts.iloc[1][1]

    def test_yearly_to_monthly(self):
        ts_data = create_test_data(AllFrequencies.Y, 5)
        ts = TimeSeries(ts_data, "Y")
        expanded_ts = ts.expand("M", "ffill")
        assert len(expanded_ts) == 49
        assert expanded_ts.frequency.name == "monthly"
        assert expanded_ts.iloc[0][1] == expanded_ts.iloc[1][1]


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
    def test_daily_ts(self):
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
    def test_daily_ts(self):
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

    def test_weekly_ts(self):
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
