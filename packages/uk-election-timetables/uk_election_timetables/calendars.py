import json
import os
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from enum import Enum
from typing import List

from uk_election_timetables.date import DateMatcher, days_before


class Country(Enum):
    """
    The countries of the United Kingdom.
    """

    ENGLAND = 1
    NORTHERN_IRELAND = 2
    SCOTLAND = 3
    WALES = 4


class Region(Enum):
    """
    The regions of the United Kingdom and Gibraltar as elected in the EU Parliament
    """

    EAST_MIDLANDS = 1
    EAST_OF_ENGLAND = 2
    LONDON = 3
    NORTH_EAST_ENGLAND = 4
    NORTH_WEST_ENGLAND = 5
    NORTHERN_IRELAND = 6
    SCOTLAND = 7
    SOUTH_EAST_ENGLAND = 8
    SOUTH_WEST_ENGLAND = 9
    WALES = 10
    WEST_MIDLANDS = 11
    YORKSHIRE_AND_THE_HUMBER = 12


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
        event_date = datetime.strptime(entry["date"], "%Y-%m-%d")

        return DateMatcher(
            name=entry["title"],
            year=event_date.year,
            month=event_date.month,
            day=event_date.day,
        )

    def __init__(self, dates):
        christmas_eve = DateMatcher(month=12, day=24)

        days_not_counted = [
            BankHolidayCalendar.create_matcher_from_entry(entry)
            for entry in dates
        ]

        self._bank_holidays = days_not_counted

        self._exempted_dates = self._bank_holidays + [christmas_eve]

    def exempted_dates(self):
        return self._exempted_dates


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
            for d in rule.generate(y, base._bank_holidays)
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

        Fortunately the Gov.UK bank holidays are consistently labelled
        """
        for bh in bank_holidays:
            if bh.year != year:
                continue
            if bh.name == "Good Friday":
                good_friday = date(bh.year, bh.month, bh.day)
                easter_monday = good_friday + timedelta(days=3)
                return [
                    DateMatcher(
                        name="Easter Monday",
                        year=easter_monday.year,
                        month=easter_monday.month,
                        day=easter_monday.day,
                    )
                ]
        return []


def working_days_before(
    end_date: date, days: int, calendar: BaseCalendar
) -> date:
    """
    Return date corresponding to `count` working days before `poll_date` according to the given bank holiday calendar

    :param end_date: the date of the poll
    :param days: the number of days before the poll date
    :param calendar: the bank holiday calendar used in the calculation
    :return: the calculated date
    """

    return days_before(end_date, days, calendar.exempted_dates())
