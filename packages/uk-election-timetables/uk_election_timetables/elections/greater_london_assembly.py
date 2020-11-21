from datetime import date

from uk_election_timetables.calendars import working_days_before
from uk_election_timetables.election import Election


class GreaterLondonAssemblyElection(Election):
    def __init__(self, poll_date: date):
        self.poll_date = poll_date

    def sopn_publish_date(self) -> date:
        """
        Calculate the publish date for an election to the Greater London Assembly

        This is set out in `The Greater London Authority Elections (Amendment) Rules 2016 <https://www.legislation.gov.uk/uksi/2016/24/article/6/made>`_

        :param poll_date: a datetime representing the date of the poll
        :return: a datetime representing the expected publish date
        """
        return working_days_before(
            self.poll_date, 23, type(self).BANK_HOLIDAY_CALENDAR.england_and_wales()
        )
