# from fincal.core import FincalOptions
from fincal.fincal import TimeSeries

data = [
    ("2022-01-01", 10),
    ("2022-01-02", 12),
    ("2022-01-03", 14),
    ("2022-01-04", 16),
    ("2022-01-06", 18),
    ("2022-01-07", 20),
    ("2022-01-09", 22),
    ("2022-01-10", 24),
    ("2022-01-11", 26),
    ("2022-01-13", 28),
    ("2022-01-14", 30),
    ("2022-01-15", 32),
    ("2022-01-16", 34),
]
ts = TimeSeries(data, frequency="D")
print(ts)

data = [("2022-01-01", 220), ("2022-01-08", 230), ("2022-01-15", 240)]
ts2 = TimeSeries(data, frequency="W")
print(ts2)

synced_ts = ts.sync(ts2)
print("---------\n")
for i in synced_ts:
    print(i)
