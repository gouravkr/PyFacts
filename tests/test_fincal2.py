import datetime
import math
import random

import pytest
from fincal.exceptions import DateNotFoundError
from fincal.fincal import TimeSeries, create_date_series
from fincal.utils import FincalOptions


def create_prices(s0: float, mu: float, sigma: float, num_prices: int) -> list:
    """Generates a price following a geometric brownian motion process based on the input of the arguments:
    - s0: Asset inital price.
    - mu: Interest rate expressed annual terms.
    - sigma: Volatility expressed annual terms.
    - seed: seed for the random number generator
    - num_prices: number of prices to generate
    """

    random.seed(1234)  # WARNING! Changing the seed will cause most tests to fail
    all_values = []
    for _ in range(num_prices):
        s0 *= math.exp(
            (mu - 0.5 * sigma**2) * (1.0 / 365.0) + sigma * math.sqrt(1.0 / 365.0) * random.gauss(mu=0, sigma=1)
        )
        all_values.append(round(s0, 2))

    return all_values


def create_data():
    """Creates TimeSeries data"""

    dates = create_date_series("2017-01-01", "2020-10-31", "D", skip_weekends=True)
    values = create_prices(1000, 0.1, 0.05, 1000)
    ts = TimeSeries(dict(zip(dates, values)), frequency="D")
    return ts


class TestReturns:
    def test_returns_calc(self):
        ts = create_data()
        returns = ts.calculate_returns(
            "2020-01-01", annual_compounded_returns=False, interval_type="years", interval_value=1
        )
        assert round(returns[1], 6) == 0.112913

        returns = ts.calculate_returns(
            "2020-04-01", annual_compounded_returns=False, interval_type="months", interval_value=3
        )
        assert round(returns[1], 6) == 0.015908

        returns = ts.calculate_returns(
            "2020-04-01", annual_compounded_returns=True, interval_type="months", interval_value=3
        )
        assert round(returns[1], 6) == 0.065167

        returns = ts.calculate_returns(
            "2020-04-01", annual_compounded_returns=False, interval_type="days", interval_value=90
        )
        assert round(returns[1], 6) == 0.017673

        returns = ts.calculate_returns(
            "2020-04-01", annual_compounded_returns=True, interval_type="days", interval_value=90
        )
        assert round(returns[1], 6) == 0.073632

        with pytest.raises(DateNotFoundError):
            ts.calculate_returns("2020-04-04", interval_type="days", interval_value=90, as_on_match="exact")
        with pytest.raises(DateNotFoundError):
            ts.calculate_returns("2020-04-04", interval_type="months", interval_value=3, prior_match="exact")

    def test_date_formats(self):
        ts = create_data()
        FincalOptions.date_format = "%d-%m-%Y"
        with pytest.raises(ValueError):
            ts.calculate_returns("2020-04-10", annual_compounded_returns=True, interval_type="days", interval_value=90)

        returns1 = ts.calculate_returns("2020-04-01", interval_type="days", interval_value=90, date_format="%Y-%m-%d")
        returns2 = ts.calculate_returns("01-04-2020", interval_type="days", interval_value=90)
        assert round(returns1[1], 6) == round(returns2[1], 6) == 0.073632

        FincalOptions.date_format = "%m-%d-%Y"
        with pytest.raises(ValueError):
            ts.calculate_returns("2020-04-01", annual_compounded_returns=True, interval_type="days", interval_value=90)

        returns1 = ts.calculate_returns("2020-04-01", interval_type="days", interval_value=90, date_format="%Y-%m-%d")
        returns2 = ts.calculate_returns("04-01-2020", interval_type="days", interval_value=90)
        assert round(returns1[1], 6) == round(returns2[1], 6) == 0.073632

    def test_limits(self):
        ts = create_data()
        FincalOptions.date_format = "%Y-%m-%d"
        with pytest.raises(DateNotFoundError):
            ts.calculate_returns("2020-11-25", interval_type="days", interval_value=90, closest_max_days=10)
