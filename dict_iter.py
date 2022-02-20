import pandas

from fincal.fincal import TimeSeries

dfd = pandas.read_csv('test_files/nav_history_daily - Copy.csv')
dfm = pandas.read_csv('test_files/nav_history_monthly.csv')

data_d = [(i.date, i.nav) for i in dfd.itertuples() if i.amfi_code == 118825]
data_d.sort()
data_m = [{'date': i.date, 'value': i.nav} for i in dfm.itertuples()]

tsd = TimeSeries(data_d, frequency='D')

md = dict(data_d)
counter = 1
for i in iter(md):
    print(i)
    counter += 1
    if counter >= 5: break

print('\n')
counter = 1
for i in reversed(md):
    print('rev', i)
    counter += 1
    if counter >= 5: break

x = [next(i) for i in iter(md)]
print(x)
