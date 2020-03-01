from sopn_publish_date.date import days_before
from datetime import date


def test_zero_days_before():
    example = date(2020, 1, 1)

    assert days_before(example, 0) == example
