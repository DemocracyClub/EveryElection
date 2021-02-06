from datetime import date

from uk_election_timetables.calendars import working_days_before, Country
from uk_election_timetables.election import Election


class SeneddCymruElection(Election):
    def __init__(self, poll_date: date):
        Election.__init__(self, poll_date, Country.WALES)

    @property
    def sopn_publish_date(self) -> date:
        """
        Calculate the publish date for an election to the Senedd Cymru / Welsh Parliament

        This is set out in `Senedd and Elections (Wales) Act 2020 <https://www.legislation.gov.uk/anaw/2020/1/contents>` and `The National Assembly for Wales (Representation of the People) (Amendment) Order 2016 <https://www.legislation.gov.uk/uksi/2016/272/article/18/made>`_

        :param poll_date: a datetime representing the date of the poll
        :return: a datetime representing the expected publish date
        """
        return working_days_before(self.poll_date, 19, super()._calendar())
