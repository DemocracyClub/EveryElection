import datetime as dt

import pytest

from uk_election_timetables.calendars import Country, UnitedKingdomBankHolidays
from uk_election_timetables.elections import CityOfLondonLocalElection
from uk_election_timetables.elections.city_of_london_local import (
    ChristmasBreakRule,
    EasterBreakRule,
)

registration_test_cases = [
    {
        "poll_date": dt.date(2025, 1, 1),
        "expected_registration_deadline": dt.date(2023, 11, 30),
    },
    {
        "poll_date": dt.date(2025, 2, 15),
        "expected_registration_deadline": dt.date(2023, 11, 30),
    },
    {
        "poll_date": dt.date(2025, 2, 16),
        "expected_registration_deadline": dt.date(2024, 11, 30),
    },
    {
        "poll_date": dt.date(2025, 11, 29),
        "expected_registration_deadline": dt.date(2024, 11, 30),
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
        "poll_date": dt.date(2022, 9, 15),
        "sopn_publish_date": dt.date(2022, 8, 23),
    },
    {
        # https://candidates.democracyclub.org.uk/elections/local.city-of-london.bassishaw.by.2019-04-30/sopn/
        # includes an easter break
        "poll_date": dt.date(2019, 4, 30),
        "sopn_publish_date": dt.date(2019, 4, 2),
    },
    {
        # https://candidates.democracyclub.org.uk/elections/local.city-of-london-alder.cornhill.2022-05-26/sopn/
        "poll_date": dt.date(2022, 5, 26),
        "sopn_publish_date": dt.date(2022, 5, 4),
    },
]


@pytest.mark.parametrize("election", sopn_test_cases)
def test_city_of_london_sopn_date(election):
    assert (
        CityOfLondonLocalElection(election["poll_date"]).sopn_publish_date
        == election["sopn_publish_date"]
    )


def test_notice_of_election_deadline():
    """
    note: this test is just reverse-engineered from the code

    There is no local.city-of-london.2021-05-06

    Replace it with a test based on a real-world example
    when we have one to hand.
    """
    election = CityOfLondonLocalElection(dt.date(2021, 5, 6))

    assert election.notice_of_election_deadline == dt.date(2021, 3, 25)


def test_easter_break():
    rule = EasterBreakRule()
    # Test by example: 2022
    # Easter Sunday = April 17
    # Easter Sunday 2022 = April 17
    # Break: April 14 (Thu) through April 19 (Tue) = 6 days
    bank_holidays = (
        UnitedKingdomBankHolidays().from_country(Country.ENGLAND)._bank_holidays
    )
    matchers = rule.generate(2022, bank_holidays)
    assert len(matchers) == 6
    dates = {(m.year, m.month, m.day) for m in matchers}
    assert (2022, 4, 14) in dates  # Thursday before Good Friday
    assert (2022, 4, 15) in dates  # Good Friday
    assert (2022, 4, 17) in dates  # Easter Sunday
    assert (2022, 4, 18) in dates  # Easter Monday
    assert (2022, 4, 19) in dates  # Tuesday after Easter


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


def test_christmas_break_2014():
    # In 2014, Christmas and Boxing day are Friday and Saturday
    # The next available weekday is Monday 29th
    bank_holidays = (
        UnitedKingdomBankHolidays().from_country(Country.ENGLAND)._bank_holidays
    )
    christmas_break_matchers = ChristmasBreakRule().generate(
        2014, bank_holidays
    )
    assert _contains_matcher_for_date(
        christmas_break_matchers, dt.date(2014, 12, 24)
    )
    assert _contains_matcher_for_date(
        christmas_break_matchers, dt.date(2014, 12, 29)
    )


def test_christmas_break_2021():
    # In 2021, Christmas and Boxing day both fall at the weekend
    # with substitute bank holidays on the 27th and 28th
    bank_holidays = (
        UnitedKingdomBankHolidays().from_country(Country.ENGLAND)._bank_holidays
    )
    christmas_break_matchers = ChristmasBreakRule().generate(
        2021, bank_holidays
    )
    assert _contains_matcher_for_date(
        christmas_break_matchers, dt.date(2021, 12, 24)
    )
    assert _contains_matcher_for_date(
        christmas_break_matchers, dt.date(2021, 12, 29)
    )


def test_christmas_break_2022():
    # In 2022, Christmas day falls on Sunday
    # with a substitute bank holiday on the 27th
    bank_holidays = (
        UnitedKingdomBankHolidays().from_country(Country.ENGLAND)._bank_holidays
    )
    christmas_break_matchers = ChristmasBreakRule().generate(
        2022, bank_holidays
    )
    assert _contains_matcher_for_date(
        christmas_break_matchers, dt.date(2022, 12, 23)
    )
    assert _contains_matcher_for_date(
        christmas_break_matchers, dt.date(2022, 12, 28)
    )


def test_christmas_break_2024():
    # In 2024, Christmas Eve, Christmas Day, Boxing day and the 27th are all weekdays
    bank_holidays = (
        UnitedKingdomBankHolidays().from_country(Country.ENGLAND)._bank_holidays
    )
    christmas_break_matchers = ChristmasBreakRule().generate(
        2024, bank_holidays
    )
    assert _contains_matcher_for_date(
        christmas_break_matchers, dt.date(2024, 12, 24)
    )
    assert _contains_matcher_for_date(
        christmas_break_matchers, dt.date(2024, 12, 27)
    )
