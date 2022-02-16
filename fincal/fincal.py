import datetime
import pandas as pd
from typing import Union, Dict, List, Iterable, Any


class TimeSeries:
    def __init__(
        self,
        data=List[tuple],
        date_format: str = '%Y-%m-%d',
        frequency='infer'  # D, W, M, Q, H, Y
    ):
        self.time_series = [(datetime.datetime.strptime(i[0], date_format), i[1]) for i in data]
        self.dates = {i[0] for i in self.time_series}

#     def infer_frequency(self):
#         sample_dates = [i[0] for i in self.time_series[:10]]
#         for i in sample_dates
    def __repr__(self):
        if len(self.time_series) > 6:
            printable_data_1 = self.time_series[:3]
            printable_data_2 = self.time_series[-3:]
            printable_str = "TimeSeries([{}\n\t...\n\t{}])".format(
                ',\n\t'.join([str(i) for i in printable_data_1]),
                ',\n\t'.join([str(i) for i in printable_data_2])
            )
        else:
            printable_data = self.time_series
            printable_str = "TimeSeries([{}])".format(',\n\t'.join([str(i) for i in printable_data]))
        return printable_str

    def __str__(self):
        if len(self.time_series) > 6:
            printable_data_1 = self.time_series[:3]
            printable_data_2 = self.time_series[-3:]
            printable_str = "[{}\n ...\n {}]".format(
                ',\n '.join([str(i) for i in printable_data_1]),
                ',\n '.join([str(i) for i in printable_data_2])
            )
        else:
            printable_data = self.time_series
            printable_str = "[{}]".format(',\n '.join([str(i) for i in printable_data]))
        return printable_str

    def ffill(self):
        new_ts = []
        for dt, val in self.time_series:
            if dt == self.time_series[0][0]:
                new_ts.append((dt, val))
            else:
                diff = (dt - prev_date).days
                if diff != 1:
                    for k in range(1, diff):
                        new_ts.append((prev_date + datetime.timedelta(days=k), prev_val))
                new_ts.append((dt, val))
            prev_date = dt
            prev_val = val
        self.ffilled_time_series = new_ts
        return self.ffilled_time_series

    def bfill(self):
        new_ts = []
        for dt, val in self.time_series[::-1]:
            if dt == self.time_series[-1][0]:
                new_ts.append((dt, val))
            else:
                diff = (prev_date - dt).days
                if diff != 1:
                    for k in range(1, diff):
                        new_ts.append((prev_date - datetime.timedelta(days=k), prev_val))
                new_ts.append((dt, val))
            prev_date = dt
            prev_val = val
        self.ffilled_time_series = new_ts[::-1]
        return self.ffilled_time_series

    def calculate_returns(
        self,
        as_on: datetime.date,
        closest: str = 'previous',
        compounding: bool = True,
        years: int = 1
    ) -> int:
        """Method to calculate returns for a certain time-period as on a particular date
            >>> calculate_returns(datetime.date(2020, 1, 1), years=1)
        """

        current = [(dt, val) for dt, val in self.time_series if dt == as_on][0]
        if not current:
            raise ValueError("As on date not found")

        prev_date = as_on.replace(year=as_on.year-years)
        if closest == 'previous':
            previous = [(dt, val) for dt, val in self.time_series if dt <= prev_date][-1]
        elif closest == 'next':
            previous = [(dt, val) for dt, val in self.time_series if dt >= prev_date][0]
#         print(current, previous)

        returns = current[1]/previous[1]
        if compounding:
            returns = returns ** (1/years)
        return returns - 1

    def calculate_rolling_returns(
        self,
        from_date: datetime.date,
        to_date: datetime.date,
        frequency: str = 'd',
        closest: str = 'previous',
        compounding: bool = True,
        years: int = 1
    ) -> List[tuple]:
        """Calculates the rolling return"""

        datediff = (to_date - from_date).days
        dates = []
        for i in range(datediff):
            if from_date + datetime.timedelta(days=i) in self.dates:
                dates.append(from_date + datetime.timedelta(days=i))

        rolling_returns = []
        for i in dates:
            returns = self.calculate_returns(as_on=i, compounding=compounding, years=years, closest=closest)
            rolling_returns.append((i, returns))
        self.rolling_returns = rolling_returns
        return self.rolling_returns
