
import unittest

from fincal.fincal import TimeSeries


class TestFincal(unittest.TestCase):
    def test_ts(self):
        data = [
            ('2020-01-01',  23),
            ('2020-01-02',  24),
            ('2020-01-03',  25),
            ('2020-01-06',  26),
            ('2020-01-07',  27),
            ('2020-01-08',  28),
            ('2020-01-10',  29),
            ('2020-01-11',  30)
        ]
        time_series = TimeSeries(data)
        time_series.ffill(inplace=True)
        self.assertEqual(len(time_series.time_series), 11)
