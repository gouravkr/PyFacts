import datetime

from fincal.core import Series

s1 = Series([2.5, 6.2, 5.6, 8.4, 7.4, 1.5, 9.6, 5])

dt_lst = [
    datetime.datetime(2020, 12, 4, 0, 0),
    datetime.datetime(2019, 5, 16, 0, 0),
    datetime.datetime(2019, 9, 25, 0, 0),
    datetime.datetime(2016, 2, 18, 0, 0),
    datetime.datetime(2017, 8, 14, 0, 0),
    datetime.datetime(2018, 1, 4, 0, 0),
    datetime.datetime(2017, 5, 21, 0, 0),
    datetime.datetime(2018, 7, 17, 0, 0),
    datetime.datetime(2016, 4, 8, 0, 0),
    datetime.datetime(2020, 1, 7, 0, 0),
    datetime.datetime(2016, 12, 24, 0, 0),
    datetime.datetime(2020, 6, 19, 0, 0),
    datetime.datetime(2016, 3, 16, 0, 0),
    datetime.datetime(2017, 4, 25, 0, 0),
    datetime.datetime(2016, 7, 10, 0, 0)
]

s2 = Series(dt_lst)
