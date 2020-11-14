from abc import ABCMeta, abstractmethod
from datetime import date

from uk_election_timetables.calendars import UnitedKingdomBankHolidays


class Election(metaclass=ABCMeta):
    BANK_HOLIDAY_CALENDAR = UnitedKingdomBankHolidays()

    @abstractmethod
    def sopn_publish_date(self) -> date:
        pass
