from datetime import date, timedelta
from typing import List

SATURDAY = 5
SUNDAY = 6
WEEKEND = [SATURDAY, SUNDAY]


class DateMatcher:
    """
    An object that represents a matcher against datetime.date objects, given a day,
    a month, and an optional year.
    """

    def __init__(
        self, day: int, month: int, year: int = None, name: str = None
    ):
        self.name = name
        self.month = month
        self.day = day
        self.year = year

    def matches(self, other: date) -> bool:
        """
        Return whether the input date matches the attributes of this class

        :param other: the date being matched against
        :return: a boolean representing if the input date matches this class's attributes
        """
        if self.day != other.day:
            return False

        if self.month != other.month:
            return False

        if self.year is not None and self.year != other.year:
            return False

        return True


def days_before(
    poll_date: date, days: int, ignore: List[DateMatcher] = None
) -> date:
    """
    Return date corresponding to `days` working days before `poll_date`, not counting the list of provided exemptions

    :param poll_date: the date of the poll
    :param days: the number of days before the poll date
    :param ignore: the list of DateMatchers to ignore in the look-back calculation
    :return: the calculated date
    """

    while days > 0:
        poll_date -= timedelta(days=1)

        if poll_date.weekday() in WEEKEND:
            continue

        if ignore and any(day.matches(poll_date) for day in ignore):
            continue

        days -= 1

    return poll_date
