from abc import ABCMeta, abstractmethod
from datetime import date
from typing import Dict, List

from uk_election_timetables.calendars import UnitedKingdomBankHolidays, Country


class Election(metaclass=ABCMeta):
    BANK_HOLIDAY_CALENDAR = UnitedKingdomBankHolidays()

    def __init__(self, poll_date: date, country: Country):
        self.poll_date = poll_date
        self.country = country

    @property
    @abstractmethod
    def sopn_publish_date(self) -> date:
        pass

    @property
    def timetable(self) -> List[Dict]:
        """
        An aggregate of all known dates for the specific election type.

        :return: a list representing the entire timetable for this particular election.
        """
        return [
            {
                "label": "List of candidates published",
                "date": self.sopn_publish_date,
            }
        ]

    def _calendar(self):
        return self.BANK_HOLIDAY_CALENDAR.from_country(self.country)
