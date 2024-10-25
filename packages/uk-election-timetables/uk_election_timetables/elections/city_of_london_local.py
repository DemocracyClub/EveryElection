from datetime import date

from uk_election_timetables.calendars import working_days_before, Country
from uk_election_timetables.election import Election


"""
TODO:
This is insufficently nuanced
https://github.com/DemocracyClub/uk-election-timetables/issues/8
"""


class CityOfLondonLocalElection(Election):
    def __init__(self, poll_date: date):
        Election.__init__(self, poll_date, Country.ENGLAND)

    @property
    def sopn_publish_date(self) -> date:
        """
        Calculate the SOPN publish date for a City of London local election.

        :return: a datetime representing the expected publish date
        """

        return working_days_before(self.poll_date, 17, super()._calendar())

    @property
    def registration_deadline(self) -> date:
        """
        Calculates the voter registration deadline for a City of London local election.

        :return: a datetime representing the voter registration deadline
        """
        if self.poll_date <= date(self.poll_date.year, 2, 15):
            return date(self.poll_date.year - 2, 11, 30)
        return date(self.poll_date.year - 1, 11, 30)
