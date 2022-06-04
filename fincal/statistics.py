import datetime
import statistics
from typing import Literal

from fincal.core import date_parser

from .fincal import TimeSeries
from .utils import _interval_to_years


@date_parser(3, 4)
def sharpe_ratio(
    time_series_data: TimeSeries,
    risk_free_data: TimeSeries = None,
    risk_free_rate: float = None,
    from_date: str | datetime.datetime = None,
    to_date: str | datetime.datetime = None,
    frequency: Literal["D", "W", "M", "Q", "H", "Y"] = None,
    return_period_unit: Literal["years", "months", "days"] = "years",
    return_period_value: int = 1,
    as_on_match: str = "closest",
    prior_match: str = "closest",
    closest: Literal["previous", "next"] = "previous",
    date_format: str = None,
):
    """Calculate the Sharpe ratio of any time series

    Sharpe ratio is a measure of returns per unit of risk,
    where risk is measured by the standard deviation of the returns.

    Parameters
    ----------
    time_series_data:
        The time series for which Sharpe ratio needs to be calculated

    risk_free_data:
        Risk free rates as time series data.
        This should be the time series of risk free returns,
        and not the underlying asset value.

    risk_free_rate:
        Risk free rate to be used.
        Either risk_free_data or risk_free_rate needs to be provided.
        If both are provided, the time series data will be used.

    from_date:
        Start date from which returns should be calculated.
        Defaults to the first date of the series.

    to_date:
        End date till which returns should be calculated.
        Defaults to the last date of the series.

    frequency:
        The frequency at which returns should be calculated.

    return_period_unit : 'years', 'months', 'days'
        The type of time period to use for return calculation.

    return_period_value : int
        The value of the specified interval type over which returns needs to be calculated.

    as_on_match:

    prior_match :

    closest :

    date_format :

    Returns
    -------
        _description_

    Raises
    ------
    ValueError
        _description_
    """
    interval_days = int(_interval_to_years(return_period_unit, return_period_value) * 365 + 1)

    if from_date is None:
        from_date = time_series_data.start_date + datetime.timedelta(days=interval_days)
    if to_date is None:
        to_date = time_series_data.end_date

    if risk_free_data is None and risk_free_rate is None:
        raise ValueError("At least one of risk_free_data or risk_free rate is required")
    elif risk_free_data is not None:
        risk_free_rate = risk_free_data.mean()

    common_params = {
        "from_date": from_date,
        "to_date": to_date,
        "frequency": frequency,
        "return_period_unit": return_period_unit,
        "return_period_value": return_period_value,
        "as_on_match": as_on_match,
        "prior_match": prior_match,
        "closest": closest,
        "date_format": date_format,
    }
    average_rr = time_series_data.average_rolling_return(**common_params, annual_compounded_returns=True)

    excess_returns = average_rr - risk_free_rate
    sd = time_series_data.volatility(
        **common_params,
        annualize_volatility=True,
    )

    sharpe_ratio_value = excess_returns / sd
    return sharpe_ratio_value


@date_parser(2, 3)
def beta(
    asset_data: TimeSeries,
    market_data: TimeSeries,
    from_date: str | datetime.datetime = None,
    to_date: str | datetime.datetime = None,
    frequency: Literal["D", "W", "M", "Q", "H", "Y"] = None,
    return_period_unit: Literal["years", "months", "days"] = "years",
    return_period_value: int = 1,
    as_on_match: str = "closest",
    prior_match: str = "closest",
    closest: Literal["previous", "next"] = "previous",
    date_format: str = None,
):
    interval_years = _interval_to_years(return_period_unit, return_period_value)
    interval_days = int(interval_years * 365 + 1)

    annual_compounded_returns = True if interval_years > 1 else False

    if from_date is None:
        from_date = asset_data.start_date + datetime.timedelta(days=interval_days)
    if to_date is None:
        to_date = asset_data.end_date

    common_params = {
        "from_date": from_date,
        "to_date": to_date,
        "frequency": frequency,
        "return_period_unit": return_period_unit,
        "return_period_value": return_period_value,
        "as_on_match": as_on_match,
        "prior_match": prior_match,
        "closest": closest,
        "date_format": date_format,
        "annual_compounded_returns": annual_compounded_returns,
    }

    asset_rr = asset_data.calculate_rolling_returns(**common_params)
    market_rr = market_data.calculate_rolling_returns(**common_params)

    cov = statistics.covariance(asset_rr.values, market_rr.values)
    market_var = statistics.variance(market_rr.values)

    beta = cov / market_var
    return beta
