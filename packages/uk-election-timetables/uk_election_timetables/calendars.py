import datetime as dt
import json
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import List

from uk_election_timetables.date import DateMatcher, days_diff, easter_sunday


class Country(Enum):
    """
    The countries of the United Kingdom.
    """

    ENGLAND = 1
    NORTHERN_IRELAND = 2
    SCOTLAND = 3
    WALES = 4


class BaseCalendar(ABC):
    @abstractmethod
    def exempted_dates(self):
        pass


class BankHolidayCalendar(BaseCalendar):
    """
    A calendar that excludes the input list of dates.
    """

    @staticmethod
    def create_matcher_from_entry(entry: dict) -> DateMatcher:
        event_date = dt.datetime.strptime(entry["date"], "%Y-%m-%d")

        return DateMatcher(
            name=entry["title"],
            year=event_date.year,
            month=event_date.month,
            day=event_date.day,
        )

    def __init__(self, dates):
        days_not_counted = [
            BankHolidayCalendar.create_matcher_from_entry(entry)
            for entry in dates
        ]

        self._bank_holidays = days_not_counted

    def exempted_dates(self):
        return self._bank_holidays


class UnitedKingdomBankHolidays:
    """
    A representation of the bank holiday calendars in the United Kingdom.

    This class exposes a function for each unique calendar: England & Wales, Northern Ireland, and Scotland.
    """

    def __init__(self):
        self._calendar = {}

        bank_holiday_json = os.path.join(
            os.path.dirname(__file__), "bank-holidays.json"
        )

        with open(bank_holiday_json, "r", encoding="utf-8") as data:
            json_calendar = json.loads(data.read())

            for country in json_calendar:
                self._calendar[country] = BankHolidayCalendar(
                    json_calendar[country]["events"]
                )

    def england_and_wales(self) -> BankHolidayCalendar:
        """
        :return: a calendar representation of bank holidays in England and Wales
        """
        return self._calendar["england-and-wales"]

    def scotland(self) -> BankHolidayCalendar:
        """
        :return: a calendar representation of bank holidays in Scotland
        """
        return self._calendar["scotland"]

    def northern_ireland(self) -> BankHolidayCalendar:
        """
        :return: a calendar representation of bank holidays in Northern Ireland
        """
        return self._calendar["northern-ireland"]

    def from_country(self, country: Country) -> BankHolidayCalendar:
        """
        Return the bank holiday calendar for the input country.

        :param country: the country to retrieve the calendar for
        :return: the corresponding calendar
        """
        if country == Country.ENGLAND or country == Country.WALES:
            return self.england_and_wales()
        if country == Country.NORTHERN_IRELAND:
            return self.northern_ireland()
        return self.scotland()


class ExcludedDateRule(ABC):
    @abstractmethod
    def generate(
        self, year: int, bank_holidays: List[DateMatcher]
    ) -> List[DateMatcher]:
        pass


class ExtendedCalendar(BaseCalendar):
    """
    Wraps a BankHolidayCalendar and layers additional ExcludedDateRules on top.

    Also implements the BaseCalendar ABC so we can drop it in as a
    replacement for BankHolidayCalendar.
    """

    def __init__(
        self,
        base: BankHolidayCalendar,
        rules: List[ExcludedDateRule],
        years: List[int],
    ):
        extra = [
            d
            for rule in rules
            for y in years
            for d in rule.generate(y, base.exempted_dates())
        ]
        self._all_dates = base.exempted_dates() + extra

    def exempted_dates(self):
        return self._all_dates


class EasterMondayRule(ExcludedDateRule):
    def generate(
        self, year: int, bank_holidays: List[DateMatcher]
    ) -> List[DateMatcher]:
        """
        Easter Monday is not usually a bank holiday in Scotland but some
        legislation considers it a "non-working" day in Scotland anyway.

        This rule allows us to easily extend the Scotland holiday
        calendar when necessary.
        """
        easter_monday = easter_sunday(year) + dt.timedelta(days=1)
        return [
            DateMatcher(
                name="Easter Monday",
                year=easter_monday.year,
                month=easter_monday.month,
                day=easter_monday.day,
            )
        ]


class ChristmasEveRule(ExcludedDateRule):
    def generate(
        self, year: int, bank_holidays: List[DateMatcher]
    ) -> List[DateMatcher]:
        """
        Christmas Eve is a bank holiday but most legislation
        explicity considers it a "non-working" day anyway.
        """
        return [DateMatcher(name="Christmas Eve", year=year, month=12, day=24)]


def working_days_before(
    end_date: dt.date, days: int, calendar: BaseCalendar
) -> dt.date:
    """
    Return date corresponding to `count` working days before `poll_date` according to the given bank holiday calendar

    :param end_date: the date of the poll
    :param days: the number of days before the poll date
    :param calendar: the bank holiday calendar used in the calculation
    :return: the calculated date
    """

    return days_diff(end_date, 0 - days, calendar.exempted_dates())


def working_days_after(
    base_date: dt.date, days: int, calendar: BaseCalendar
) -> dt.date:
    """
    Return date corresponding to `count` working days after `base_date` according to the given bank holiday calendar

    :param base_date: the date to count from
    :param days: the number of days to count
    :param calendar: the bank holiday calendar used in the calculation
    :return: the calculated date
    """

    return days_diff(base_date, days, calendar.exempted_dates())
