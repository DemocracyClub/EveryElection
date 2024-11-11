from datetime import date

from uk_election_timetables.date import DateMatcher, days_before


def test_zero_days_before():
    example = date(2020, 1, 1)

    assert days_before(example, 0) == example


def test_non_zero_days_before():
    example = date(2020, 1, 1)

    assert days_before(example, 1) == date(2019, 12, 31)
    assert days_before(example, 2) == date(2019, 12, 30)


def test_ignore_weekends():
    example = date(2020, 1, 6)  # Monday

    assert days_before(example, 1) == date(2020, 1, 3)


def test_ignore_exempted_day_with_year():
    example = date(2020, 1, 1)

    exempted_dates = [DateMatcher(year=2019, month=12, day=31)]

    assert days_before(example, 1, exempted_dates) == date(2019, 12, 30)


def test_ignore_exempted_day_without_year():
    example = date(2020, 1, 1)

    exempted_dates = [DateMatcher(month=12, day=31)]

    assert days_before(example, 1, exempted_dates) == date(2019, 12, 30)
