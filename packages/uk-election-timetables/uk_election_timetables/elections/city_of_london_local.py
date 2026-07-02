import datetime as dt
from typing import List

from uk_election_timetables.calendars import (
    Country,
    ExcludedDateRule,
    working_days_before,
)
from uk_election_timetables.date import WEEKEND, DateMatcher, easter_sunday
from uk_election_timetables.election import Election


def _is_bank_holiday(date: dt.date, bank_holidays: List[DateMatcher]) -> bool:
    return any(bh.matches(date) for bh in bank_holidays)


class EasterBreakRule(ExcludedDateRule):
    def generate(
        self, year: int, bank_holidays: List[DateMatcher]
    ) -> List[DateMatcher]:
        """
        “the Easter break” means the period beginning with the Thursday before
        and ending with the Tuesday after Easter Day
        """
        easter_break = []
        maundy_thursday = easter_sunday(year) - dt.timedelta(days=3)
        for offset in range(0, 6):
            day = maundy_thursday + dt.timedelta(days=offset)
            easter_break.append(
                DateMatcher(
                    name="City of London Easter Break",
                    year=day.year,
                    month=day.month,
                    day=day.day,
                )
            )
        return easter_break


class ChristmasBreakRule(ExcludedDateRule):
    def generate(
        self, year: int, bank_holidays: List[DateMatcher]
    ) -> List[DateMatcher]:
        """
        “the Christmas break” means the period beginning with the last week day
        before Christmas Day and ending with the first week day after Christmas
        Day which is not a bank holiday
        """
        christmas_break = []

        break_start = dt.date(year, 12, 24)
        while break_start.weekday() in WEEKEND:
            break_start -= dt.timedelta(days=1)

        break_end = dt.date(year, 12, 27)
        while break_end.weekday() in WEEKEND or _is_bank_holiday(
            break_end, bank_holidays
        ):
            break_end += dt.timedelta(days=1)

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
            current_date += dt.timedelta(days=1)
        return christmas_break


class CityOfLondonLocalElection(Election):
    def __init__(self, poll_date: dt.date):
        """
        :param poll_date: datetime.date representing the date of the poll
        """
        Election.__init__(self, poll_date, Country.ENGLAND)

    @property
    def close_of_nominations(self) -> dt.date:
        """
        Calculate the "SOPN publish date" for a City of London local election.

        As well as the usual exclusions for weekends and bank holidays,
        the City of London also exclude a Christmas break and Easter break.

        In this section “the Christmas break” means the period beginning with
        the last week day before Christmas Day and ending with the first week
        day after Christmas Day which is not a bank holiday; “the Easter break”
        means the period beginning with the Thursday before and ending with the
        Tuesday after Easter Day;

        Note: There is an additional way that City of London is unusual here.

        For all other election types, the withdrawal deadline aligns with
        close_of_nominations. For City of London, it lines up with the
        sopn_publish_deadline.

        This means the first SOPN can be _published_
        **17 (working) days before polling day**
        but then candidates can be withdrawn from it for an additional day
        after that.
        So the SOPN becomes _final_ **16 (working) days before polling day**

        :return: datetime.date representing the expected publish date
        """

        calendar = self.get_extended_calendar(
            [EasterBreakRule(), ChristmasBreakRule()]
        )
        return working_days_before(self.poll_date, 17, calendar)

    @property
    def registration_deadline(self) -> dt.date:
        """
        Calculates the voter registration deadline for a City of London local election.

        :return: datetime.date representing the voter registration deadline
        """
        if self.poll_date <= dt.date(self.poll_date.year, 2, 15):
            return dt.date(self.poll_date.year - 2, 11, 30)
        return dt.date(self.poll_date.year - 1, 11, 30)

    @property
    def notice_of_election_deadline(self) -> dt.date:
        """
        Calculate the deadline for publishing a Notice of Election document for City of London Common Council or Alderman election

        The same exceptions for Christmas and Easter breaks that we use for the SOPN date apply here.

        :return: a datetime.date representing the expected publish date
        """
        calendar = self.get_extended_calendar(
            [EasterBreakRule(), ChristmasBreakRule()]
        )
        return working_days_before(self.poll_date, 25, calendar)
