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


def test_easter_monday_rule():
    rule = EasterMondayRule()
    # Test by example: 2022
    # Easter Sunday = April 17
    # Easter Monday = April 18
    bank_holidays = (
        UnitedKingdomBankHolidays().from_country(Country.ENGLAND)._bank_holidays
    )
    matchers = rule.generate(2022, bank_holidays)

    assert len(matchers) == 1
    matcher = matchers[0]
    date_ = (matcher.year, matcher.month, matcher.day)
    assert date_ == (2022, 4, 18)
