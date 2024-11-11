from datetime import date, datetime, timedelta
from typing import List

from uk_election_timetables.calendars import (
    Country,
    UnitedKingdomBankHolidays,
    working_days_before,
)
from uk_election_timetables.date import WEEKEND, DateMatcher
from uk_election_timetables.election import Election


def _is_bank_holiday(date: date, bank_holidays: List[DateMatcher]) -> bool:
    for bh in bank_holidays:
        if bh.matches(date):
            return True
    return False


def _get_easter_break(bank_holidays: List[DateMatcher]) -> List[DateMatcher]:
    """
    “the Easter break” means the period beginning with the Thursday before
    and ending with the Tuesday after Easter Day

    Fortunately the Gov.UK bank holidays are consistently labelled
    """
    easter_break = []
    for bh in bank_holidays:
        if bh.name == "Good Friday":
            good_friday = date(bh.year, bh.month, bh.day)
            for offset in range(-1, 5):
                day = good_friday + timedelta(days=offset)
                easter_break.append(
                    DateMatcher(
                        name="City of London Easter Break",
                        year=day.year,
                        month=day.month,
                        day=day.day,
                    )
                )
    return easter_break


def _get_christmas_break(bank_holidays: List[DateMatcher]) -> List[DateMatcher]:
    """
    “the Christmas break” means the period beginning with the last week day
    before Christmas Day and ending with the first week day after Christmas
    Day which is not a bank holiday
    """
    christmas_break = []

    # 2012 is the first year that exists in our bank holiday calendar
    # so we won't go any further back than that
    beginning_of_time = 2012
    current_year = datetime.now().year

    for year in range(beginning_of_time, current_year + 1):
        break_start = date(year, 12, 24)
        while break_start.weekday() in WEEKEND:
            break_start -= timedelta(days=1)

        break_end = date(year, 12, 27)
        while break_end.weekday() in WEEKEND or _is_bank_holiday(
            break_end, bank_holidays
        ):
            break_end += timedelta(days=1)

        current_date = break_start
        while current_date <= break_end:
            christmas_break.append(
                DateMatcher(
                    name="City of London Christmas Break",
                    year=current_date.year,
                    month=current_date.month,
                    day=current_date.day,
                )
            )
            current_date += timedelta(days=1)
    return christmas_break


class CityOfLondonLocalElection(Election):
    def __init__(self, poll_date: date):
        """
        :param poll_date: a datetime representing the date of the poll
        """
        Election.__init__(self, poll_date, Country.ENGLAND)

    @property
    def sopn_publish_date(self) -> date:
        """
        Calculate the "SOPN publish date" for a City of London local election.

        There are actually 2 releavant dates here:
        The SOPN is _published_ **17 (working) days before polling day**
        but then candidates can be withdrawn from it for an additional day
        after that.
        So the SOPN becomes _final_ **16 (working) days before polling day**

        For the sake of simplicity, we are going to call 16 days before
        polling day the "sopn_publish_date".

        As well as the usual exclusions for weekends and bank holidays,
        the City of London also exclude a Christmas break and Easter break.

        In this section “the Christmas break” means the period beginning with
        the last week day before Christmas Day and ending with the first week
        day after Christmas Day which is not a bank holiday; “the Easter break”
        means the period beginning with the Thursday before and ending with the
        Tuesday after Easter Day;

        :return: a datetime representing the expected publish date
        """

        # Make a new calendar object so we don't mutate
        # the shared England & Wales calendar
        calendar = UnitedKingdomBankHolidays().from_country(Country.ENGLAND)

        # Add the City of London Christmas and Easter breaks
        # This will result in some duplication in _exempted_dates
        # where existing bank holidays are also inside these intervals
        # but this doesn't really matter
        calendar._exempted_dates = (
            calendar._exempted_dates
            + _get_easter_break(calendar._bank_holidays)
            + _get_christmas_break(calendar._bank_holidays)
        )

        return working_days_before(self.poll_date, 16, calendar)

    @property
    def registration_deadline(self) -> date:
        """
        Calculates the voter registration deadline for a City of London local election.

        :return: a datetime representing the voter registration deadline
        """
        if self.poll_date <= date(self.poll_date.year, 2, 15):
            return date(self.poll_date.year - 2, 11, 30)
        return date(self.poll_date.year - 1, 11, 30)
