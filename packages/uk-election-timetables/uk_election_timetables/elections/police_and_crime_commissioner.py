from datetime import date

from uk_election_timetables.calendars import working_days_before, Country
from uk_election_timetables.election import Election


class PoliceAndCrimeCommissionerElection(Election):
    def __init__(self, poll_date: date):
        Election.__init__(self, poll_date, Country.ENGLAND)

    @property
    def sopn_publish_date(self) -> date:
        """
        Calculate the publish date for an election to the position of Police and Crime Commissioner

        This is set out in `The Police and Crime Commissioner Elections (Amendment) Order 2014 <https://www.legislation.gov.uk/uksi/2014/921/article/31/made>`_

        :param poll_date: a datetime representing the date of the poll
        :return: a datetime representing the expected publish date
        """
        return working_days_before(self.poll_date, 18, super()._calendar())
