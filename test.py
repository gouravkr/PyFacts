# type: ignore

import datetime
import time

import pandas as pd

from fincal.fincal import TimeSeries

df = pd.read_csv('test_files/nav_history_daily.csv')
df = df.sort_values(by=['amfi_code', 'date'])  # type: ignore
data_list = [(i.date, i.nav) for i in df[df.amfi_code == 118825].itertuples()]

start = time.time()
ts_data = TimeSeries(data_list, frequency='M')
print(f"Instantiation took {round((time.time() - start)*1000, 2)} ms")
# ts_data.fill_missing_days()
start = time.time()
# ts_data.calculate_returns(as_on=datetime.datetime(2022, 1, 4), closest='next', years=1)
rr = ts_data.calculate_rolling_returns(datetime.datetime(2015, 1, 1),
                                       datetime.datetime(2022, 1, 21),
                                       frequency='M',
                                       as_on_match='next',
                                       prior_match='previous',
                                       closest='previous',
                                       years=1)

# ffill_data = ts_data.bfill()
print(f"Calculation took {round((time.time() - start)*1000, 2)} ms")
rr.sort()
for i in rr[:10]:
    print(i)
# print(ffill_data)
# print(ts_data)
# print(repr(ts_data))
