import datetime
import math
import random

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


def create_test_timeseries(
    frequency: Frequency, num: int = 1000, skip_weekends: bool = False, mu: float = 0.1, sigma: float = 0.05
) -> TimeSeries:
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
        frequency.freq_type: int(frequency.value * num * (7 / 5 if frequency == "D" and skip_weekends else 1))
    }
    end_date = start_date + relativedelta(**timedelta_dict)
    dates = create_date_series(start_date, end_date, frequency.symbol, skip_weekends=skip_weekends)
    values = create_prices(1000, mu, sigma, num)
    ts = TimeSeries(dict(zip(dates, values)), frequency=frequency.symbol)
    return ts


class TestReturns:
    def test_returns_calc(self):
        ts = create_test_timeseries()
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
        ts = create_test_timeseries()
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
        ts = create_test_timeseries()
        with pytest.raises(DateNotFoundError):
            ts.calculate_returns("2020-11-25", return_period_unit="days", return_period_value=90, closest_max_days=10)


class TestVolatility:
    def test_daily_ts(self):
        ts = create_test_timeseries(AllFrequencies.D)
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
