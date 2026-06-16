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


def easter_sunday(year: int) -> date:
    # Compute Easter Sunday for a given year using Revised Gregorian algorithm
    # vendored from dateutil
    y = year
    g = y % 19
    e = 0
    c = y // 100
    h = (c - c // 4 - (8 * c + 13) // 25 + 19 * g + 15) % 30
    i = h - (h // 28) * (1 - (h // 28) * (29 // (h + 1)) * ((21 - g) // 11))
    j = (y + y // 4 + i + 2 - c + c // 4) % 7
    p = i - j + e
    d = 1 + (p + 27 + (p + 6) // 40) % 31
    m = 3 + (p + 26) // 30
    return date(int(y), int(m), int(d))
