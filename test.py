# from fincal.core import FincalOptions
import fincal as fc

data = [
    ("2022-01-01", 150),
    ("2022-01-02", 152),
    ("2022-01-03", 151),
    ("2022-01-04", 154),
    ("2022-01-05", 150),
    ("2022-01-06", 157),
    ("2022-01-07", 155),
    ("2022-01-08", 158),
    ("2022-01-09", 162),
    ("2022-01-10", 160),
    ("2022-01-11", 156),
    ("2022-01-12", 162),
    ("2023-01-01", 164),
    ("2023-01-02", 161),
    ("2023-01-03", 167),
    ("2023-01-04", 168),
]
ts = fc.TimeSeries(data, frequency="D", date_format="%Y-%d-%m")
print(ts)

sharpe = fc.sharpe_ratio(
    ts,
    risk_free_rate=(1 + 0.15) ** (1 / 12) - 1,
    from_date="2022-02-01",
    to_date="2023-04-01",
    frequency="M",
    return_period_unit="months",
    return_period_value=1,
)
print(f"{sharpe=}")
