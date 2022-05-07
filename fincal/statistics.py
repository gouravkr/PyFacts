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
