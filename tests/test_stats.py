import pyfacts as pft


def test_conf(conf_fun):
    conf_add = conf_fun
    assert conf_add(2, 4) == 6


class TestSharpe:
    def test_sharpe_daily_freq(self, create_test_data):
        data = create_test_data(num=1305, frequency=pft.AllFrequencies.D, skip_weekends=True)
        ts = pft.TimeSeries(data, "D")
        sharpe_ratio = pft.sharpe_ratio(
            ts,
            risk_free_rate=0.06,
            from_date="2017-02-04",
            to_date="2021-12-31",
            return_period_unit="months",
            return_period_value=1,
        )
        assert round(sharpe_ratio, 4) == 1.0502

        sharpe_ratio = pft.sharpe_ratio(
            ts,
            risk_free_rate=0.06,
            from_date="2017-01-09",
            to_date="2021-12-31",
            return_period_unit="days",
            return_period_value=7,
        )
        assert round(sharpe_ratio, 4) == 1.0701

        sharpe_ratio = pft.sharpe_ratio(
            ts,
            risk_free_rate=0.06,
            from_date="2018-01-02",
            to_date="2021-12-31",
            return_period_unit="years",
            return_period_value=1,
        )
        assert round(sharpe_ratio, 4) == 1.4374

        sharpe_ratio = pft.sharpe_ratio(
            ts,
            risk_free_rate=0.06,
            from_date="2017-07-03",
            to_date="2021-12-31",
            return_period_unit="months",
            return_period_value=6,
        )
        assert round(sharpe_ratio, 4) == 0.8401

    def test_sharpe_weekly_freq(self, create_test_data):
        data = create_test_data(num=261, frequency=pft.AllFrequencies.W, mu=0.6, sigma=0.7)
        ts = pft.TimeSeries(data, "W")
        sharpe_ratio = pft.sharpe_ratio(
            ts,
            risk_free_rate=0.052,
            from_date="2017-01-08",
            to_date="2021-12-31",
            return_period_unit="days",
            return_period_value=7,
        )
        assert round(sharpe_ratio, 4) == 0.4533

        sharpe_ratio = pft.sharpe_ratio(
            ts,
            risk_free_rate=0.052,
            from_date="2017-02-05",
            to_date="2021-12-31",
            return_period_unit="months",
            return_period_value=1,
        )
        assert round(sharpe_ratio, 4) == 0.4898

        sharpe_ratio = pft.sharpe_ratio(
            ts,
            risk_free_rate=0.052,
            from_date="2018-01-01",
            to_date="2021-12-31",
            return_period_unit="months",
            return_period_value=12,
        )
        assert round(sharpe_ratio, 4) == 0.3199


class TestBeta:
    def test_beta_daily_freq(self, create_test_data):
        market_data = create_test_data(num=3600, frequency=pft.AllFrequencies.D)
        stock_data = create_test_data(num=3600, frequency=pft.AllFrequencies.D, mu=0.12, sigma=0.08)
        sts = pft.TimeSeries(stock_data, "D")
        mts = pft.TimeSeries(market_data, "D")
        beta = pft.beta(sts, mts, frequency="D", return_period_unit="days", return_period_value=1)
        assert round(beta, 4) == 1.6001

    def test_beta_daily_freq_daily_returns(self, create_test_data):
        market_data = create_test_data(num=3600, frequency=pft.AllFrequencies.D)
        stock_data = create_test_data(num=3600, frequency=pft.AllFrequencies.D, mu=0.12, sigma=0.08)
        sts = pft.TimeSeries(stock_data, "D")
        mts = pft.TimeSeries(market_data, "D")
        beta = pft.beta(sts, mts)
        assert round(beta, 4) == 1.6292

    def test_beta_monthly_freq(self, create_test_data):
        market_data = create_test_data(num=3600, frequency=pft.AllFrequencies.D)
        stock_data = create_test_data(num=3600, frequency=pft.AllFrequencies.D, mu=0.12, sigma=0.08)
        sts = pft.TimeSeries(stock_data, "D")
        mts = pft.TimeSeries(market_data, "D")
        beta = pft.beta(sts, mts, frequency="M")
        assert round(beta, 4) == 1.629

    def test_beta_monthly_freq_monthly_returns(self, create_test_data):
        market_data = create_test_data(num=3600, frequency=pft.AllFrequencies.D)
        stock_data = create_test_data(num=3600, frequency=pft.AllFrequencies.D, mu=0.12, sigma=0.08)
        sts = pft.TimeSeries(stock_data, "D")
        mts = pft.TimeSeries(market_data, "D")
        beta = pft.beta(sts, mts, frequency="M", return_period_unit="months", return_period_value=1)
        assert round(beta, 4) == 1.6023
