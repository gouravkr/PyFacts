import datetime
import math
import random

# import time
from typing import List

from dateutil.relativedelta import relativedelta

import pyfacts as pft


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


def sample_data_generator(
    frequency: pft.Frequency,
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
            frequency.value * num * (7 / 5 if frequency == pft.AllFrequencies.D and skip_weekends else 1)
        )
    }
    end_date = start_date + relativedelta(**timedelta_dict)
    dates = pft.create_date_series(start_date, end_date, frequency.symbol, skip_weekends=skip_weekends, eomonth=eomonth)
    values = create_prices(1000, mu, sigma, num)
    ts = list(zip(dates, values))
    return ts


market_data = sample_data_generator(num=3600, frequency=pft.AllFrequencies.D, skip_weekends=False)
mts = pft.TimeSeries(market_data, "D")
print(mts)

# print("Datediff=", (mts.end_date - mts.start_date).days)
# stock_data = sample_data_generator(num=3600, frequency=pft.AllFrequencies.D, skip_weekends=False, mu=0.12, sigma=0.15)
# sts = pft.TimeSeries(stock_data, "D")
# print(sts)

# start = time.time()
# alpha = pft.jensens_alpha(
#     asset_data=sts, market_data=mts, risk_free_rate=0.052, return_period_unit="months", return_period_value=1
# )

# print(alpha)

# print("Alpha calculation took", time.time() - start, "seconds")

# print("Correlation=", pft.correlation(sts, mts))

rr = mts.calculate_rolling_returns(frequency="D")

print(117, rr[rr.values < 0.1])
