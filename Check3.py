import datetime
import math
import random
import time
from typing import List

from dateutil.relativedelta import relativedelta

import pyfacts as pft

data = [
    ("2021-01-01", 10),
    ("2021-02-01", 12),
    ("2021-03-01", 14),
    ("2021-04-01", 16),
    ("2021-05-01", 18),
    ("2021-06-01", 20),
]

ts = pft.TimeSeries(data)
print(repr(ts))
