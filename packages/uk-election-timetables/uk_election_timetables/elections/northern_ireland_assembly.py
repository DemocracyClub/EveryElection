import datetime as dt

from uk_election_timetables.calendars import Country, working_days_before
from uk_election_timetables.election import Election


class NorthernIrelandAssemblyElection(Election):
    def __init__(self, poll_date: dt.date):
        """
        :param poll_date: a datetime representing the date of the poll
        """
        Election.__init__(self, poll_date, Country.NORTHERN_IRELAND)

    @property
    def sopn_publish_date(self) -> dt.date:
        """
        Calculate the publish date for an election to the Northern Ireland Assembly

        This is set out by Schedule 5, Rules 1 and 2 of `The Northern Ireland Assembly (Elections) (Amendment) Order 2009 <https://www.legislation.gov.uk/uksi/2009/256/made>`_

        :return: a datetime representing the expected publish date
        """
        return working_days_before(self.poll_date, 16, super()._calendar())

    @property
    def notice_of_election_deadline(self) -> dt.date:
        """
        Calculate the deadline for publishing a Notice of Election document for an election to the Northern Ireland Assembly

        This is set out by Schedule 5, Rules 1 and 2 of `The Northern Ireland Assembly (Elections) (Amendment) Order 2009 <https://www.legislation.gov.uk/uksi/2009/256/made>`_

        :return: datetime.date representing the deadline to publish
        """
        return working_days_before(self.poll_date, 25, super()._calendar())
