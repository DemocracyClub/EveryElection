import datetime as dt

from uk_election_timetables.calendars import (
    Country,
    EasterMondayRule,
    UnitedKingdomBankHolidays,
)

uk_calendars = UnitedKingdomBankHolidays()

scotland = uk_calendars.scotland()
england_and_wales = uk_calendars.england_and_wales()
northern_ireland = uk_calendars.northern_ireland()


def test_should_separate_by_country():
    should_not_contain_holiday(england_and_wales, "St Patrick’s Day")

    should_not_contain_holiday(
        scotland, "Battle of the Boyne (Orangemen’s Day)"
    )

    should_not_contain_holiday(northern_ireland, "St Andrew’s Day")


def should_not_contain_holiday(calendar, name):
    assert not [
        holiday for holiday in calendar.exempted_dates() if holiday.name == name
    ]


def test_easter_monday_rule_2022():
    rule = EasterMondayRule()
    # Easter 2022
    # Good Friday = April 15
    # Easter Monday = April 18
    bank_holidays = (
        UnitedKingdomBankHolidays().from_country(Country.ENGLAND)._bank_holidays
    )
    matchers = rule.generate(2022, bank_holidays)

    assert len(matchers) == 1
    matcher = matchers[0]
    date_ = (matcher.year, matcher.month, matcher.day)
    assert date_ == (2022, 4, 18)


def test_easter_monday_rule_current_year():
    # Assert that we've got a matcher object for the current year.
    # If there were some future year where Good Friday wasn't labelled
    # with "Good Friday" in the gov.uk data, we'd have zero matchers
    # for that year. this test would catch it and fail.
    bank_holidays = (
        UnitedKingdomBankHolidays().from_country(Country.ENGLAND)._bank_holidays
    )
    rule = EasterMondayRule()
    matchers = rule.generate(dt.datetime.now().year, bank_holidays)
    assert len(matchers) == 1
