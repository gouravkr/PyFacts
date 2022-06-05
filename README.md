# PyFacts
PyFacts stands for Python library for Financial analysis and computations on time series. It is a library which makes it simple to work with time series data.

Most libraries, and languages like SQL, work with rows. Operations are performed by rows and not by dates. For instance, to calculate 1-year rolling returns in SQL, you are forced to use either a lag of 365/252 rows, leading to an approximation, or slow and cumbersome joins. PyFacts solves this by allowing you to work with dates and time intervals. Hence, to calculate 1-year returns, you will be specifying a lag of 1-year and the library will do the grunt work of finding the most appropriate observations to calculate these returns on.

## The problem
Libraries and languages usually don't allow comparison based on dates. Calculating month on month or year on year returns are always cumbersome as users are forced to rely on row lags. However, data always have inconsistencies, especially financial data. Markets don't work on weekends, there are off days, data doesn't get released on a few days a year, data availability is patchy when dealing with 40-year old data. All these problems are exacerbated when you are forced to make calculations using lag.

## The Solution
PyFacts aims to simplify things by allowing you to:
* Compare time-series data based on dates and time-period-based lag
* Easy way to work around missing dates by taking the closest data points
* Completing series with missing data points using forward fill and backward fill
* Use friendly dates everywhere written as a simple string

## Creating a time series
Time series data can be created from a dictionary, a list of lists/tuples/dicts, or by reading a csv file.

Example:
```
>>> import pyfacts as pft

>>> time_series_data = [
...    ('2021-01-01', 10),
...    ('2021-02-01', 12),
...    ('2021-03-01', 14),
...    ('2021-04-01', 16),
...    ('2021-05-01', 18),
...    ('2021-06-01', 20)
...]

>>> ts = fc.TimeSeries(time_series_data)
```

### Sample usage
```
>>> ts.calculate_returns(as_on='2021-04-01', return_period_unit='months', return_period_value=3, annual_compounded_returns=False)
(datetime.datetime(2021, 4, 1, 0, 0), 0.6)

>>> ts.calculate_returns(as_on='2021-04-15', return_period_unit='months', return_period_value=3, annual_compounded_returns=False)
(datetime.datetime(2021, 4, 1, 0, 0), 0.6)
```

### Working with dates
With PyFacts, you never have to go into the hassle of creating datetime objects for your time series. PyFacts will parse any date passed to it as string. The default format is ISO format, i.e., YYYY-MM-DD. However, you can use your preferred format simply by specifying it in the options in datetime library compatible format, after importing the library. For example, to use DD-MM-YYY format:

```
>>> import pyfacts as pft
>>> fc.PyfactsOptions.date_format = '%d-%m-%Y'
```
Now the library will automatically parse all dates as DD-MM-YYYY

If you happen to have any one situation where you need to use a different format, all methods accept a date_format parameter to override the default.

## To-do

### Core features
- [x] Add __setitem__
- [ ] Create emtpy TimeSeries object
- [x] Read from CSV
- [ ] Write to CSV
- [x] Convert to dict
- [x] Convert to list of tuples

### pyfacts features
- [x] Sync two TimeSeries
- [x] Average rolling return
- [x] Sharpe ratio
- [x] Jensen's Alpha
- [x] Beta
- [ ] Sortino ratio
- [x] Correlation & R-squared
- [ ] Treynor ratio
- [x] Max drawdown
- [ ] Moving average

### Pending implementation
- [x] Use limit parameter in ffill and bfill
- [x] Implementation of ffill and bfill may be incorrect inside expand, check and correct
- [ ] Implement interpolation in expand