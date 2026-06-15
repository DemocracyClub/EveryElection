import datetime as dt

import pytest

from uk_election_timetables.date import DateMatcher, days_before, easter_sunday


def test_zero_days_before():
    example = dt.date(2020, 1, 1)

    assert days_before(example, 0) == example


def test_non_zero_days_before():
    example = dt.date(2020, 1, 1)

    assert days_before(example, 1) == dt.date(2019, 12, 31)
    assert days_before(example, 2) == dt.date(2019, 12, 30)


def test_ignore_weekends():
    example = dt.date(2020, 1, 6)  # Monday

    assert days_before(example, 1) == dt.date(2020, 1, 3)


def test_ignore_exempted_day_with_year():
    example = dt.date(2020, 1, 1)

    exempted_dates = [DateMatcher(year=2019, month=12, day=31)]

    assert days_before(example, 1, exempted_dates) == dt.date(2019, 12, 30)


def test_ignore_exempted_day_without_year():
    example = dt.date(2020, 1, 1)

    exempted_dates = [DateMatcher(month=12, day=31)]

    assert days_before(example, 1, exempted_dates) == dt.date(2019, 12, 30)


# vendored from dateutil
easter_dates = [
    dt.date(1990, 4, 15),
    dt.date(1991, 3, 31),
    dt.date(1992, 4, 19),
    dt.date(1993, 4, 11),
    dt.date(1994, 4, 3),
    dt.date(1995, 4, 16),
    dt.date(1996, 4, 7),
    dt.date(1997, 3, 30),
    dt.date(1998, 4, 12),
    dt.date(1999, 4, 4),
    dt.date(2000, 4, 23),
    dt.date(2001, 4, 15),
    dt.date(2002, 3, 31),
    dt.date(2003, 4, 20),
    dt.date(2004, 4, 11),
    dt.date(2005, 3, 27),
    dt.date(2006, 4, 16),
    dt.date(2007, 4, 8),
    dt.date(2008, 3, 23),
    dt.date(2009, 4, 12),
    dt.date(2010, 4, 4),
    dt.date(2011, 4, 24),
    dt.date(2012, 4, 8),
    dt.date(2013, 3, 31),
    dt.date(2014, 4, 20),
    dt.date(2015, 4, 5),
    dt.date(2016, 3, 27),
    dt.date(2017, 4, 16),
    dt.date(2018, 4, 1),
    dt.date(2019, 4, 21),
    dt.date(2020, 4, 12),
    dt.date(2021, 4, 4),
    dt.date(2022, 4, 17),
    dt.date(2023, 4, 9),
    dt.date(2024, 3, 31),
    dt.date(2025, 4, 20),
    dt.date(2026, 4, 5),
    dt.date(2027, 3, 28),
    dt.date(2028, 4, 16),
    dt.date(2029, 4, 1),
    dt.date(2030, 4, 21),
    dt.date(2031, 4, 13),
    dt.date(2032, 3, 28),
    dt.date(2033, 4, 17),
    dt.date(2034, 4, 9),
    dt.date(2035, 3, 25),
    dt.date(2036, 4, 13),
    dt.date(2037, 4, 5),
    dt.date(2038, 4, 25),
    dt.date(2039, 4, 10),
    dt.date(2040, 4, 1),
    dt.date(2041, 4, 21),
    dt.date(2042, 4, 6),
    dt.date(2043, 3, 29),
    dt.date(2044, 4, 17),
    dt.date(2045, 4, 9),
    dt.date(2046, 3, 25),
    dt.date(2047, 4, 14),
    dt.date(2048, 4, 5),
    dt.date(2049, 4, 18),
    dt.date(2050, 4, 10),
]


@pytest.mark.parametrize("easter_date", easter_dates)
def test_easter(easter_date):
    assert easter_date == easter_sunday(easter_date.year)
