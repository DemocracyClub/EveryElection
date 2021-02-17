from abc import ABCMeta, abstractmethod
from datetime import date
from typing import Dict, List

from uk_election_timetables.calendars import (
    UnitedKingdomBankHolidays,
    Country,
    working_days_before,
)


class Election(metaclass=ABCMeta):
    BANK_HOLIDAY_CALENDAR = UnitedKingdomBankHolidays()

    def __init__(self, poll_date: date, country: Country):
        self.poll_date = poll_date
        self.country = country

    @property
    def postal_vote_application_deadline(self) -> date:
        """
        Calculates the postal vote application deadline for this Election

        This is set out in `The Representation of the People (England and Wales) Regulations 2001 <https://www.legislation.gov.uk/uksi/2001/341/regulation/56/made>`_.

        :return: a datetime representing the postal vote application deadline
        """
        return working_days_before(self.poll_date, 11, self._calendar())

    @property
    @abstractmethod
    def sopn_publish_date(self) -> date:
        pass

    @property
    def registration_deadline(self) -> date:
        """
        Calculates the voter registration deadline for this Election

        This explained in a `background note from the Electoral Commission <https://www.electoralcommission.org.uk/media/2457>`_

        :return: a datetime representing the voter registration deadline
        """
        return working_days_before(self.poll_date, 12, self._calendar())

    @property
    def timetable(self) -> List[Dict]:
        """
        An aggregate of all known dates for the specific election type.

        :return: a list representing the entire timetable for this particular election.
        """
        return sorted(
            [
                {
                    "label": "Register to vote deadline",
                    "date": self.registration_deadline,
                },
                {
                    "label": "List of candidates published",
                    "date": self.sopn_publish_date,
                },
                {
                    "label": "Postal vote application deadline",
                    "date": self.postal_vote_application_deadline,
                },
            ],
            key=lambda r: r["date"],
        )

    def _calendar(self):
        return self.BANK_HOLIDAY_CALENDAR.from_country(self.country)
