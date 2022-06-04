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
) -> float:
    """Calculate the Sharpe ratio of any time series

    Sharpe ratio is a measure of returns per unit of risk,
    where risk is measured by the standard deviation of the returns.

    The formula for Sharpe ratio is:
        (average asset return - risk free rate)/volatility of asset returns

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

    return_period_unit: 'years', 'months', 'days'
        The type of time period to use for return calculation.

    return_period_value: int
        The value of the specified interval type over which returns needs to be calculated.

    as_on_match: str, optional
            The mode of matching the as_on_date. Refer closest.

    prior_match: str, optional
        The mode of matching the prior_date. Refer closest.

    closest: str, optional
        The mode of matching the closest date.
        Valid values are 'exact', 'previous', 'next' and next.

    The date format to use for this operation.
            Should be passed as a datetime library compatible string.
            Sets the date format only for this operation. To set it globally, use FincalOptions.date_format

    Returns
    -------
        Value of Sharpe ratio as a float.

    Raises
    ------
    ValueError
        If risk free data or risk free rate is not provided.
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
) -> float:
    """Beta is a measure of sensitivity of asset returns to market returns

    The formula for beta is:

    Parameters
    ----------
    asset_data: TimeSeries
        The time series data of the asset

    market_data: TimeSeries
        The time series data of the relevant market index

    from_date:
        Start date from which returns should be calculated.
        Defaults to the first date of the series.

    to_date:
        End date till which returns should be calculated.
        Defaults to the last date of the series.

    frequency:
        The frequency at which returns should be calculated.

    return_period_unit: 'years', 'months', 'days'
        The type of time period to use for return calculation.

    return_period_value: int
        The value of the specified interval type over which returns needs to be calculated.

    as_on_match: str, optional
            The mode of matching the as_on_date. Refer closest.

    prior_match: str, optional
        The mode of matching the prior_date. Refer closest.

    closest: str, optional
        The mode of matching the closest date.
        Valid values are 'exact', 'previous', 'next' and next.

    The date format to use for this operation.
            Should be passed as a datetime library compatible string.
            Sets the date format only for this operation. To set it globally, use FincalOptions.date_format

    Returns
    -------
        The value of beta as a float.
    """
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


@date_parser(4, 5)
def jensens_alpha(
    asset_data: TimeSeries,
    market_data: TimeSeries,
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
) -> float:
    """
    This function calculates the Jensen's alpha for a time series.
    The formula for Jensen's alpha is:
        Ri - Rf + B x (Rm - Rf)
    where:
        Ri = Realized return of the portfolio or investment
        Rf = The risk free rate during the return time frame
        B = Beta of the portfolio or investment
        Rm = Realized return of the market index

    Parameters
    ----------
    asset_data: TimeSeries
        The time series data of the asset

    market_data: TimeSeries
        The time series data of the relevant market index

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

    return_period_unit: 'years', 'months', 'days'
        The type of time period to use for return calculation.

    return_period_value: int
        The value of the specified interval type over which returns needs to be calculated.

    as_on_match: str, optional
            The mode of matching the as_on_date. Refer closest.

    prior_match: str, optional
        The mode of matching the prior_date. Refer closest.

    closest: str, optional
        The mode of matching the closest date.
        Valid values are 'exact', 'previous', 'next' and next.

    The date format to use for this operation.
            Should be passed as a datetime library compatible string.
            Sets the date format only for this operation. To set it globally, use FincalOptions.date_format

    Returns
    -------
        The value of Jensen's alpha as a float.
    """

    interval_years = _interval_to_years(return_period_unit, return_period_value)
    interval_days = int(interval_years * 365 + 1)

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
    }

    num_days = (to_date - from_date).days
    compound_realised_returns = True if num_days > 365 else False
    realized_return = asset_data.calculate_returns(
        as_on=to_date,
        return_period_unit="days",
        return_period_value=num_days,
        annual_compounded_returns=compound_realised_returns,
        as_on_match=as_on_match,
        prior_match=prior_match,
        closest=closest,
        date_format=date_format,
    )
    market_return = market_data.calculate_returns(
        as_on=to_date,
        return_period_unit="days",
        return_period_value=num_days,
        annual_compounded_returns=compound_realised_returns,
        as_on_match=as_on_match,
        prior_match=prior_match,
        closest=closest,
        date_format=date_format,
    )
    beta_value = beta(asset_data=asset_data, market_data=market_data, **common_params)

    if risk_free_data is None and risk_free_rate is None:
        raise ValueError("At least one of risk_free_data or risk_free rate is required")
    elif risk_free_data is not None:
        risk_free_rate = risk_free_data.mean()

    jensens_alpha = realized_return[1] - risk_free_rate + beta_value * (market_return[1] - risk_free_rate)
    return jensens_alpha


@date_parser(2, 3)
def correlation(
    data1: TimeSeries,
    data2: TimeSeries,
    from_date: str | datetime.datetime = None,
    to_date: str | datetime.datetime = None,
    frequency: Literal["D", "W", "M", "Q", "H", "Y"] = None,
    return_period_unit: Literal["years", "months", "days"] = "years",
    return_period_value: int = 1,
    as_on_match: str = "closest",
    prior_match: str = "closest",
    closest: Literal["previous", "next"] = "previous",
    date_format: str = None,
) -> float:
    """Calculate the correlation between two assets

    correlation calculation is done based on rolling returns.
    It must be noted that correlation is not calculated directly on the asset prices.
    The asset prices used to calculate returns and correlation is then calculated based on these returns.
    Hence this function requires all parameters for rolling returns calculations.

    Parameters
    ----------
    data1: TimeSeries
        The first time series data

    data2: TimeSeries
        The second time series data

    from_date:
        Start date from which returns should be calculated.
        Defaults to the first date of the series.

    to_date:
        End date till which returns should be calculated.
        Defaults to the last date of the series.

    frequency:
        The frequency at which returns should be calculated.

    return_period_unit: 'years', 'months', 'days'
        The type of time period to use for return calculation.

    return_period_value: int
        The value of the specified interval type over which returns needs to be calculated.

    as_on_match: str, optional
            The mode of matching the as_on_date. Refer closest.

    prior_match: str, optional
        The mode of matching the prior_date. Refer closest.

    closest: str, optional
        The mode of matching the closest date.
        Valid values are 'exact', 'previous', 'next' and next.

    The date format to use for this operation.
            Should be passed as a datetime library compatible string.
            Sets the date format only for this operation. To set it globally, use FincalOptions.date_format

    Returns
    -------
        The value of beta as a float.

    Raises
    ------
    ValueError:
        * If frequency of both TimeSeries do not match
        * If both time series do not have data between the from date and to date
    """
    interval_years = _interval_to_years(return_period_unit, return_period_value)
    interval_days = int(interval_years * 365 + 1)

    annual_compounded_returns = True if interval_years > 1 else False

    if from_date is None:
        from_date = data1.start_date + datetime.timedelta(days=interval_days)
    if to_date is None:
        to_date = data1.end_date

    if data1.frequency != data2.frequency:
        raise ValueError("Correlation calculation requires both time series to be of same frequency")

    if from_date < data2.start_date or to_date > data2.end_date:
        raise ValueError("Data between from_date and to_date must be present in both time series")

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

    asset_rr = data1.calculate_rolling_returns(**common_params)
    market_rr = data2.calculate_rolling_returns(**common_params)

    cor = statistics.correlation(asset_rr.values, market_rr.values)
    return cor
