import pandas as pd

from fincal.fincal import TimeSeries, create_date_series

dfd = pd.read_csv("test_files/nav_history_daily - Copy.csv")
dfd = dfd[dfd["amfi_code"] == 118825].reset_index(drop=True)
ts = TimeSeries([(i.date, i.nav) for i in dfd.itertuples()], frequency="D")
repr(ts)
# print(ts[['2022-01-31', '2021-05-28']])

# rr = ts.calculate_rolling_returns(from_date='2021-01-01', to_date='2022-01-01', frequency='D', interval_type='days', interval_value=30, compounding=False)


# data = [
#     ("2020-01-01", 10),
#     ("2020-02-01", 12),
#     ("2020-03-01", 14),
#     ("2020-04-01", 16),
#     ("2020-05-01", 18),
#     ("2020-06-01", 20),
#     ("2020-07-01", 22),
#     ("2020-08-01", 24),
#     ("2020-09-01", 26),
#     ("2020-10-01", 28),
#     ("2020-11-01", 30),
#     ("2020-12-01", 32),
#     ("2021-01-01", 34),
# ]

# ts = TimeSeries(data, frequency="M")
# rr = ts.calculate_rolling_returns(
#     "2020-02-01",
#     "2021-01-01",
#     if_not_found="nan",
#     compounding=False,
#     interval_type="months",
#     interval_value=1,
#     as_on_match="exact",
# )

# for i in rr:
#     print(i)

# returns = ts.calculate_returns(
#     "2020-04-25",
#     return_actual_date=True,
#     closest_max_days=15,
#     compounding=True,
#     interval_type="days",
#     interval_value=90,
#     closest="previous",
#     if_not_found="fail",
# )

# print(returns)

volatility = ts.volatility(start_date="2018-01-01", end_date="2021-01-01")
print(volatility)
