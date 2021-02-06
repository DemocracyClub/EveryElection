from datetime import date

from uk_election_timetables.calendars import working_days_before, Country
from uk_election_timetables.election import Election


class NorthernIrelandAssemblyElection(Election):
    def __init__(self, poll_date: date):
        Election.__init__(self, poll_date, Country.NORTHERN_IRELAND)

    @property
    def sopn_publish_date(self) -> date:
        """
        Calculate the publish date for an election to the Northern Ireland Assembly

        This is set out by Schedule 5, Rules 1 and 2 of `The Northern Ireland Assembly (Elections) (Amendment) Order 2009 <https://www.legislation.gov.uk/uksi/2009/256/made>`_

        :param poll_date: a datetime representing the date of the poll
        :return: a datetime representing the expected publish date
        """
        return working_days_before(self.poll_date, 16, super()._calendar())
