import fincal as fc


def test_conf(conf_fun):
    conf_add = conf_fun
    assert conf_add(2, 4) == 6


class TestSharpe:
    def test_sharpe_daily_freq(self, create_test_data):
        data = create_test_data(num=1305, frequency=fc.AllFrequencies.D, skip_weekends=True)
        ts = fc.TimeSeries(data, "D")
        sharpe_ratio = fc.sharpe_ratio(
            ts,
            risk_free_rate=0.06,
            from_date="2017-02-04",
            to_date="2021-12-31",
            return_period_unit="months",
            return_period_value=1,
        )
        assert round(sharpe_ratio, 4) == 1.0502

        sharpe_ratio = fc.sharpe_ratio(
            ts,
            risk_free_rate=0.06,
            from_date="2017-01-09",
            to_date="2021-12-31",
            return_period_unit="days",
            return_period_value=7,
        )
        assert round(sharpe_ratio, 4) == 1.0701

        sharpe_ratio = fc.sharpe_ratio(
            ts,
            risk_free_rate=0.06,
            from_date="2018-01-02",
            to_date="2021-12-31",
            return_period_unit="years",
            return_period_value=1,
        )
        assert round(sharpe_ratio, 4) == 1.4374

        sharpe_ratio = fc.sharpe_ratio(
            ts,
            risk_free_rate=0.06,
            from_date="2017-07-03",
            to_date="2021-12-31",
            return_period_unit="months",
            return_period_value=6,
        )
        assert round(sharpe_ratio, 4) == 0.8401

    def test_sharpe_weekly_freq(self, create_test_data):
        data = create_test_data(num=261, frequency=fc.AllFrequencies.W, mu=0.6, sigma=0.7)
        ts = fc.TimeSeries(data, "W")
        sharpe_ratio = fc.sharpe_ratio(
            ts,
            risk_free_rate=0.052,
            from_date="2017-01-08",
            to_date="2021-12-31",
            return_period_unit="days",
            return_period_value=7,
        )
        assert round(sharpe_ratio, 4) == 0.4533

        sharpe_ratio = fc.sharpe_ratio(
            ts,
            risk_free_rate=0.052,
            from_date="2017-02-05",
            to_date="2021-12-31",
            return_period_unit="months",
            return_period_value=1,
        )
        assert round(sharpe_ratio, 4) == 0.4898

        sharpe_ratio = fc.sharpe_ratio(
            ts,
            risk_free_rate=0.052,
            from_date="2018-01-01",
            to_date="2021-12-31",
            return_period_unit="months",
            return_period_value=12,
        )
        assert round(sharpe_ratio, 4) == 0.3199
