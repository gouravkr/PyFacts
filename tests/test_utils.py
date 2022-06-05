import datetime

import pytest
from pyfacts.utils import _interval_to_years, _parse_date


class TestParseDate:
    def test_parsing(self):
        dt = datetime.datetime(2020, 1, 1)
        assert _parse_date(dt) == dt
        assert _parse_date(dt.strftime("%Y-%m-%d")) == dt
        assert _parse_date(datetime.date(2020, 1, 1)) == dt
        assert _parse_date("01-01-2020", date_format="%d-%m-%Y") == dt
        assert _parse_date("01-01-2020", date_format="%m-%d-%Y") == dt

    def test_errors(self):
        with pytest.raises(ValueError):
            _parse_date("01-01-2020")

        with pytest.raises(ValueError):
            _parse_date("abcdefg")


class TestIntervalToYears:
    def test_months(self):
        assert _interval_to_years("months", 6) == 0.5
