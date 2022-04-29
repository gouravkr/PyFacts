from .fincal import TimeSeries


def sharpe_ratio(
    time_series_data: TimeSeries, risk_free_data: TimeSeries = None, risk_free_rate: float = None, **kwargs
):
    pass

    if risk_free_data is None and risk_free_rate is None:
        raise ValueError("At least one of risk_free_data or risk_free rate is required")

    returns_ts = time_series_data.calculate_rolling_returns(**kwargs)

    if risk_free_data is not None:
        risk_free_data = returns_ts.sync(risk_free_data)
    else:
        risk_free_data = risk_free_rate

    excess_returns = returns_ts - risk_free_data
    sd = time_series_data.volatility(**kwargs)
    sharpe_ratio = excess_returns.mean() / sd
    return sharpe_ratio
