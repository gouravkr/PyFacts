import datetime
import time
import timeit

import pandas

from pyfacts.pyfacts import AllFrequencies, TimeSeries, create_date_series

dfd = pandas.read_csv("test_files/msft.csv")
dfm = pandas.read_csv("test_files/nav_history_monthly.csv")
dfq = pandas.read_csv("test_files/nav_history_quarterly.csv")

data_d = [(i.date, i.nav) for i in dfd.itertuples()]
data_m = [{"date": i.date, "value": i.nav} for i in dfm.itertuples()]
data_q = {i.date: i.nav for i in dfq.itertuples()}
data_q.update({"14-02-2022": 93.7})

tsd = TimeSeries(data_d, frequency="D")
tsm = TimeSeries(data_m, frequency="M", date_format="%d-%m-%Y")
tsq = TimeSeries(data_q, frequency="Q", date_format="%d-%m-%Y")

start = time.time()
# ts.calculate_rolling_returns(datetime.datetime(2015, 1, 1), datetime.datetime(2022, 2, 1), years=1)
bdata = tsq.bfill()
# rr = tsd.calculate_rolling_returns(datetime.datetime(2022, 1, 1), datetime.datetime(2022, 2, 1), years=1)
print(time.time() - start)
