import datetime
from typing import Literal

from fincal.core import date_parser

from .fincal import TimeSeries


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
    pass

    if risk_free_data is None and risk_free_rate is None:
        raise ValueError("At least one of risk_free_data or risk_free rate is required")

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
    returns_ts = time_series_data.calculate_rolling_returns(**common_params, annual_compounded_returns=True)

    if risk_free_data is not None:
        risk_free_data = returns_ts.sync(risk_free_data)
    else:
        risk_free_data = risk_free_rate

    excess_returns = returns_ts - risk_free_data
    sd = time_series_data.volatility(
        **common_params,
        annualize_volatility=True,
    )

    sharpe_ratio = excess_returns.mean() / sd
    return sharpe_ratio
