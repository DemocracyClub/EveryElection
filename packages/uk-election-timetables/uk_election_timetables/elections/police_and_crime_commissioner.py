import datetime as dt

from uk_election_timetables.calendars import Country, working_days_before
from uk_election_timetables.election import Election


class PoliceAndCrimeCommissionerElection(Election):
    def __init__(self, poll_date: dt.date):
        """
        :param poll_date: a datetime representing the date of the poll
        """
        Election.__init__(self, poll_date, Country.ENGLAND)

    @property
    def sopn_publish_date(self) -> dt.date:
        """
        Calculate the publish date for an election to the position of Police and Crime Commissioner

        This is set out in `The Police and Crime Commissioner Elections (Amendment) Order 2014 <https://www.legislation.gov.uk/uksi/2014/921/article/31/made>`_

        :return: a datetime representing the expected publish date
        """
        return working_days_before(self.poll_date, 18, super()._calendar())

    @property
    def notice_of_election_deadline(self) -> dt.date:
        """
        Calculate the deadline for publishing a Notice of Election document for an election to the position of Police and Crime Commissioner

        This is set out in `The Police and Crime Commissioner Elections (Amendment) Order 2014 <https://www.legislation.gov.uk/uksi/2014/921/article/31/made>`_

        :return: datetime.date representing the deadline to publish
        """
        return working_days_before(self.poll_date, 25, super()._calendar())
