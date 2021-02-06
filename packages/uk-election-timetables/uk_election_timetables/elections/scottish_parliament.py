from datetime import date

from uk_election_timetables.calendars import working_days_before, Country
from uk_election_timetables.election import Election


class ScottishParliamentElection(Election):
    def __init__(self, poll_date: date):
        Election.__init__(self, poll_date, Country.SCOTLAND)

    @property
    def sopn_publish_date(self) -> date:
        """
        Calculate the publish date for an election to the Scottish Parliament

        This is set out in `The Scottish Parliament (Elections etc.) Order 2015 <https://www.legislation.gov.uk/ssi/2015/425/made>`_

        :param poll_date: a datetime representing the date of the poll
        :return: a datetime representing the expected publish date
        """
        return working_days_before(
            self.poll_date, 23, type(self).BANK_HOLIDAY_CALENDAR.scotland()
        )
