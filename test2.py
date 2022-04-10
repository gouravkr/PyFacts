import time

from fincal.fincal import TimeSeries

# start = time.time()
# dfd = pd.read_csv("test_files/msft.csv")  # , dtype=dict(nav=str))
# # dfd = dfd[dfd["amfi_code"] == 118825].reset_index(drop=True)
# print("instantiation took", round((time.time() - start) * 1000, 2), "ms")
# ts = TimeSeries([(i.date, i.nav) for i in dfd.itertuples()], frequency="D")
# print(repr(ts))

start = time.time()
# mdd = ts.max_drawdown()
# print(mdd)
# print("max drawdown calc took", round((time.time() - start) * 1000, 2), "ms")
# # print(ts[['2022-01-31', '2021-05-28']])

# rr = ts.calculate_rolling_returns(
#           from_date='2021-01-01',
#           to_date='2022-01-01',
#           frequency='D',
#           interval_type='days',
#           interval_value=30,
#           compounding=False
#       )


data = [
    ("2022-01-01", 10),
    # ("2022-01-08", 12),
    ("2022-01-15", 14),
    ("2022-01-22", 16)
    # ("2020-02-07", 18),
    # ("2020-02-14", 20),
    # ("2020-02-21", 22),
    # ("2020-02-28", 24),
    # ("2020-03-01", 26),
    # ("2020-03-01", 28),
    # ("2020-03-01", 30),
    # ("2020-03-01", 32),
    # ("2021-03-01", 34),
]

ts = TimeSeries(data, "W")
# ts_expanded = ts.expand("D", "ffill", skip_weekends=True)

# for i in ts_expanded:
#     print(i)

print(ts.get("2022-01-01"))

print(ts.ffill())
