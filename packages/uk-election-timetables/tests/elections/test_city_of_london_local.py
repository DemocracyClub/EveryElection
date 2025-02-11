from datetime import date, datetime

import pytest

from uk_election_timetables.calendars import Country, UnitedKingdomBankHolidays
from uk_election_timetables.elections import CityOfLondonLocalElection
from uk_election_timetables.elections.city_of_london_local import (
    _get_christmas_break,
    _get_easter_break,
)

registration_test_cases = [
    {
        "poll_date": date(2025, 1, 1),
        "expected_registration_deadline": date(2023, 11, 30),
    },
    {
        "poll_date": date(2025, 2, 15),
        "expected_registration_deadline": date(2023, 11, 30),
    },
    {
        "poll_date": date(2025, 2, 16),
        "expected_registration_deadline": date(2024, 11, 30),
    },
    {
        "poll_date": date(2025, 11, 29),
        "expected_registration_deadline": date(2024, 11, 30),
    },
]


@pytest.mark.parametrize("election", registration_test_cases)
def test_city_of_london_registration_deadline(election):
    assert (
        CityOfLondonLocalElection(election["poll_date"]).registration_deadline
        == election["expected_registration_deadline"]
    )


sopn_test_cases = [
    {
        # https://candidates.democracyclub.org.uk/elections/local.city-of-london.cordwainer.by.2022-09-15/sopn/
        "poll_date": date(2022, 9, 15),
        "sopn_publish_date": date(2022, 8, 23),
    },
    {
        # https://candidates.democracyclub.org.uk/elections/local.city-of-london.bassishaw.by.2019-04-30/sopn/
        # includes an easter break
        "poll_date": date(2019, 4, 30),
        "sopn_publish_date": date(2019, 4, 2),
    },
    {
        # https://candidates.democracyclub.org.uk/elections/local.city-of-london-alder.cornhill.2022-05-26/sopn/
        "poll_date": date(2022, 5, 26),
        "sopn_publish_date": date(2022, 5, 4),
    },
]


@pytest.mark.parametrize("election", sopn_test_cases)
def test_city_of_london_sopn_date(election):
    assert (
        CityOfLondonLocalElection(election["poll_date"]).sopn_publish_date
        == election["sopn_publish_date"]
    )


def test_get_easter_break():
    # The main thing we're asserting here is that we've got matchers objects
    # for each year. If there were some future year where Good Friday wasn't
    # labelled with "Good Friday" in the gov.uk data, we'd have zero matchers
    # for that year. this test would catch it and fail.
    easter_break_matchers = _get_easter_break(
        UnitedKingdomBankHolidays().from_country(Country.ENGLAND)._bank_holidays
    )
    beginning_of_time = 2012
    current_year = datetime.now().year
    for year in range(beginning_of_time, current_year + 1):
        assert (
            len(
                [
                    matcher
                    for matcher in easter_break_matchers
                    if matcher.year == year
                ]
            )
            == 6
        )


def _contains_matcher_for_date(matchers, date):
    return (
        len(
            [
                matcher
                for matcher in matchers
                if (matcher.year, matcher.month, matcher.day)
                == (date.year, date.month, date.day)
            ]
        )
        == 1
    )


def test_get_christmas_break_2014():
    # In 2014, Christmas and Boxing day are Friday and Saturday
    # The next available weekday is Monday 29th
    christmas_break_matchers = _get_christmas_break(
        UnitedKingdomBankHolidays().from_country(Country.ENGLAND)._bank_holidays
    )
    assert _contains_matcher_for_date(
        christmas_break_matchers, date(2014, 12, 24)
    )
    assert _contains_matcher_for_date(
        christmas_break_matchers, date(2014, 12, 29)
    )


def test_get_christmas_break_2021():
    # In 2021, Christmas and Boxing day both fall at the weekend
    # with substitute bank holidays on the 27th and 28th
    christmas_break_matchers = _get_christmas_break(
        UnitedKingdomBankHolidays().from_country(Country.ENGLAND)._bank_holidays
    )
    assert _contains_matcher_for_date(
        christmas_break_matchers, date(2021, 12, 24)
    )
    assert _contains_matcher_for_date(
        christmas_break_matchers, date(2021, 12, 29)
    )


def test_get_christmas_break_2022():
    # In 2022, Christmas day falls on Sunday
    # with a substitute bank holiday on the 27th
    christmas_break_matchers = _get_christmas_break(
        UnitedKingdomBankHolidays().from_country(Country.ENGLAND)._bank_holidays
    )
    assert _contains_matcher_for_date(
        christmas_break_matchers, date(2022, 12, 23)
    )
    assert _contains_matcher_for_date(
        christmas_break_matchers, date(2022, 12, 28)
    )


def test_get_christmas_break_2024():
    # In 2024, Christmas Eve, Christmas Day, Boxing day and the 27th are all weekdays
    christmas_break_matchers = _get_christmas_break(
        UnitedKingdomBankHolidays().from_country(Country.ENGLAND)._bank_holidays
    )
    assert _contains_matcher_for_date(
        christmas_break_matchers, date(2024, 12, 24)
    )
    assert _contains_matcher_for_date(
        christmas_break_matchers, date(2024, 12, 27)
    )
