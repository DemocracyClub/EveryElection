from uk_election_timetables.calendars import UnitedKingdomBankHolidays

uk_calendars = UnitedKingdomBankHolidays()

scotland = uk_calendars.scotland()
england_and_wales = uk_calendars.england_and_wales()
northern_ireland = uk_calendars.northern_ireland()


def test_should_separate_by_country():
    should_not_contain_holiday(england_and_wales, "St Patrick’s Day")

    should_not_contain_holiday(scotland, "Battle of the Boyne (Orangemen’s Day)")

    should_not_contain_holiday(northern_ireland, "St Andrew’s Day")


def should_not_contain_holiday(calendar, name):
    assert not [
        holiday for holiday in calendar.exempted_dates() if holiday.name == name
    ]
