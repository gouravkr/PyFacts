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

>>> ts = pft.TimeSeries(time_series_data)
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
>>> pft.PyfactsOptions.date_format = '%d-%m-%Y'
```
Now the library will automatically parse all dates as DD-MM-YYYY

If you happen to have any one situation where you need to use a different format, all methods accept a date_format parameter to override the default.


### Working with multiple time series
While working with time series data, you will often need to perform calculations on the data. PyFacts supports all kinds of mathematical operations on time series.

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

>>> ts = pft.TimeSeries(time_series_data)
>>> print(ts/100)

TimeSeries([(datetime.datetime(2022, 1, 1, 0, 0), 0.1),
	(datetime.datetime(2022, 1, 2, 0, 0), 0.12),
	(datetime.datetime(2022, 1, 3, 0, 0), 0.14),
	(datetime.datetime(2022, 1, 4, 0, 0), 0.16),
	(datetime.datetime(2022, 1, 6, 0, 0), 0.18),
	(datetime.datetime(2022, 1, 7, 0, 0), 0.2)], frequency='M')
```

Mathematical operations can also be done between time series as long as they have the same dates.

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

>>> ts = pft.TimeSeries(time_series_data)
>>> ts2 = pft.TimeSeries(time_series_data)
>>> print(ts/ts2)

TimeSeries([(datetime.datetime(2022, 1, 1, 0, 0), 1.0),
	(datetime.datetime(2022, 1, 2, 0, 0), 1.0),
	(datetime.datetime(2022, 1, 3, 0, 0), 1.0),
	(datetime.datetime(2022, 1, 4, 0, 0), 1.0),
	(datetime.datetime(2022, 1, 6, 0, 0), 1.0),
	(datetime.datetime(2022, 1, 7, 0, 0), 1.0)], frequency='M')
```

However, if the dates are not in sync, PyFacts provides convenience methods for syncronising dates.

Example:
```
>>> import pyfacts as pft

>>> data1 = [
...    ('2021-01-01', 10),
...    ('2021-02-01', 12),
...    ('2021-03-01', 14),
...    ('2021-04-01', 16),
...    ('2021-05-01', 18),
...    ('2021-06-01', 20)
...]

>>> data2 = [
...    ("2022-15-01", 20),
...    ("2022-15-02", 22),
...    ("2022-15-03", 24),
...    ("2022-15-04", 26),
...    ("2022-15-06", 28),
...    ("2022-15-07", 30)
...]

>>> ts = pft.TimeSeries(data, frequency='M', date_format='%Y-%d-%m')
>>> ts2 = pft.TimeSeries(data2, frequency='M', date_format='%Y-%d-%m')
>>> ts.sync(ts2, fill_method='bfill')  # Sync ts2 with ts1

TimeSeries([(datetime.datetime(2022, 1, 1, 0, 0), 20.0),
	(datetime.datetime(2022, 2, 1, 0, 0), 22.0),
	(datetime.datetime(2022, 3, 1, 0, 0), 24.0),
	(datetime.datetime(2022, 4, 1, 0, 0), 26.0),
	(datetime.datetime(2022, 6, 1, 0, 0), 28.0),
	(datetime.datetime(2022, 7, 1, 0, 0), 30.0)], frequency='M')
```

Even if you need to perform calculations on data with different frequencies, PyFacts will let you easily handle this with the expand and shrink methods.

Example:
```
>>> data = [
...    ("2022-01-01", 10),
...    ("2022-02-01", 12),
...    ("2022-03-01", 14),
...    ("2022-04-01", 16),
...    ("2022-05-01", 18),
...    ("2022-06-01", 20)
...]

>>> ts = pft.TimeSeries(data, 'M')
>>> ts.expand(to_frequency='W', method='ffill')

TimeSeries([(datetime.datetime(2022, 1, 1, 0, 0), 10.0),
	    (datetime.datetime(2022, 1, 8, 0, 0), 10.0),
	    (datetime.datetime(2022, 1, 15, 0, 0), 10.0)
	    ...
	    (datetime.datetime(2022, 5, 14, 0, 0), 18.0),
	    (datetime.datetime(2022, 5, 21, 0, 0), 18.0),
	    (datetime.datetime(2022, 5, 28, 0, 0), 18.0)], frequency='W')

>>> ts.shrink(to_frequency='Q', method='ffill')

TimeSeries([(datetime.datetime(2022, 1, 1, 0, 0), 10.0),
	(datetime.datetime(2022, 4, 1, 0, 0), 16.0)], frequency='Q')
```

If you want to shorten the timeframe of the data with an aggregation function, the transform method will help you out. Currently it supports sum and mean.

Example:
```
>>> data = [
...    ("2022-01-01", 10),
...    ("2022-02-01", 12),
...    ("2022-03-01", 14),
...    ("2022-04-01", 16),
...    ("2022-05-01", 18),
...    ("2022-06-01", 20),
...    ("2022-07-01", 22),
...    ("2022-08-01", 24),
...    ("2022-09-01", 26),
...    ("2022-10-01", 28),
...    ("2022-11-01", 30),
...    ("2022-12-01", 32)
...]

>>> ts = pft.TimeSeries(data, 'M')
>>> ts.transform(to_frequency='Q', method='sum')

TimeSeries([(datetime.datetime(2022, 1, 1, 0, 0), 36.0),
	(datetime.datetime(2022, 4, 1, 0, 0), 54.0),
	(datetime.datetime(2022, 7, 1, 0, 0), 72.0),
	(datetime.datetime(2022, 10, 1, 0, 0), 90.0)], frequency='Q')

>>> ts.transform(to_frequency='Q', method='mean')

TimeSeries([(datetime.datetime(2022, 1, 1, 0, 0), 12.0),
	(datetime.datetime(2022, 4, 1, 0, 0), 18.0),
	(datetime.datetime(2022, 7, 1, 0, 0), 24.0),
	(datetime.datetime(2022, 10, 1, 0, 0), 30.0)], frequency='Q')
```


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