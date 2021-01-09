from abc import ABCMeta, abstractmethod
from datetime import date
from typing import Dict, List

from uk_election_timetables.calendars import UnitedKingdomBankHolidays


class Election(metaclass=ABCMeta):
    BANK_HOLIDAY_CALENDAR = UnitedKingdomBankHolidays()

    @property
    @abstractmethod
    def sopn_publish_date(self) -> date:
        pass

    @property
    def timetable(self) -> List[Dict]:
        return [
            {
                "label": "List of candidates published",
                "date": self.sopn_publish_date,
            }
        ]
