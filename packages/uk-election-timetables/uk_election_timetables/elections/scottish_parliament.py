import datetime as dt

from uk_election_timetables.calendars import (
    Country,
    EasterMondayRule,
    working_days_before,
)
from uk_election_timetables.election import Election


class ScottishParliamentElection(Election):
    def __init__(self, poll_date: dt.date):
        """
        :param poll_date: datetime.date representing the date of the poll
        """
        Election.__init__(self, poll_date, Country.SCOTLAND)

    @property
    def postal_vote_application_deadline(self) -> dt.date:
        """
        Calculates the postal vote application deadline for this Election

        This is set out in `Scottish General Election (Coronavirus) Act 2021 <https://www.legislation.gov.uk/asp/2021/5/crossheading/postal-voting-arrangements-for-2021-election>`_.

        :return: datetime.date representing the postal vote application deadline
        """

        if self.poll_date == dt.date(2021, 5, 6):
            return working_days_before(self.poll_date, 21, super()._calendar())

        return super().postal_vote_application_deadline

    @property
    def close_of_nominations(self) -> dt.date:
        """
        Calculate the publish date for an election to the Scottish Parliament

        This is set out in `The Scottish Parliament (Elections etc.) Order 2015 <https://www.legislation.gov.uk/ssi/2015/425/made>`_

        :return: datetime.date representing the expected publish date
        """
        calendar = self.get_extended_calendar([EasterMondayRule()])
        return working_days_before(self.poll_date, 23, calendar)

    @property
    def sopn_publish_deadline(self) -> dt.date:
        calendar = self.get_extended_calendar([EasterMondayRule()])
        return working_days_before(self.poll_date, 22, calendar)

    @property
    def notice_of_election_deadline(self) -> dt.date:
        """
        Calculate the deadline for publishing a Notice of Election document for an election to the Scottish Parliament

        This is set out in `The Scottish Parliament (Elections etc.) Order 2015 <https://www.legislation.gov.uk/ssi/2015/425/made>`_

        :return: datetime.date representing the deadline to publish
        """
        calendar = self.get_extended_calendar([EasterMondayRule()])
        return working_days_before(self.poll_date, 28, calendar)
