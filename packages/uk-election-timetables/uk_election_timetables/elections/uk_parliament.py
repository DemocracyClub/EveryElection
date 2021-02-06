from datetime import date
from typing import Optional

from uk_election_timetables.calendars import working_days_before, Country
from uk_election_timetables.election import Election


class UKParliamentElection(Election):
    def __init__(self, poll_date: date, country: Country = None):
        Election.__init__(self, poll_date, country)

    @property
    def sopn_publish_date(self) -> date:
        """
        Calculate the publish date for an election to the Parliament of the United Kingdom

        This is set out in `Representation of the People Act 1983 <https://www.legislation.gov.uk/ukpga/1983/2/contents>`_ and its amendments.

        :param poll_date: a datetime representing the date of the poll
        :param country: an optional Country representing the country where the election will be held
        :return: a datetime representing the expected publish date
        """

        if self.country:
            return self.date_for_country(self.country)

        else:
            possible_dates = [
                self.date_for_country(country)
                for country in [
                    Country.ENGLAND,
                    Country.SCOTLAND,
                    Country.NORTHERN_IRELAND,
                ]
            ]

            return min(possible_dates)

    def date_for_country(self, country: Country) -> date:
        calendar = type(self).BANK_HOLIDAY_CALENDAR.from_country(country)

        return working_days_before(self.poll_date, 19, calendar)
