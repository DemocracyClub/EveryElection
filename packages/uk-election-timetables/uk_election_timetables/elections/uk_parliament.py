import datetime as dt

from uk_election_timetables.calendars import (
    ChristmasEveRule,
    Country,
    ExtendedCalendar,
    working_days_before,
)
from uk_election_timetables.election import Election


class UKParliamentElection(Election):
    def __init__(self, poll_date: dt.date, country: Country = None):
        """
        :param poll_date: datetime.date representing the date of the poll
        :param country: an optional Country representing the country where the election will be held
        """
        Election.__init__(self, poll_date, country)

    @property
    def sopn_publish_date(self) -> dt.date:
        """
        Calculate the publish date for an election to the Parliament of the United Kingdom

        This is set out in `Representation of the People Act 1983 <https://www.legislation.gov.uk/ukpga/1983/2/contents>`_ and its amendments.

        :return: datetime.date representing the expected publish date
        """

        days_prior = 19

        if self.country:
            return self.date_for_country(days_prior, self.country)

        possible_dates = [
            self.date_for_country(days_prior, country)
            for country in [
                Country.ENGLAND,
                Country.SCOTLAND,
                Country.NORTHERN_IRELAND,
            ]
        ]
        return min(possible_dates)

    @property
    def notice_of_election_deadline(self) -> dt.date:
        """
        Calculate the deadline for publishing a Notice of Election document for an election to the Parliament of the United Kingdom

        :return: datetime.date representing the deadline to publish
        """

        days_prior = 22

        if self.country:
            return self.date_for_country(days_prior, self.country)

        possible_dates = [
            self.date_for_country(days_prior, country)
            for country in [
                Country.ENGLAND,
                Country.SCOTLAND,
                Country.NORTHERN_IRELAND,
            ]
        ]
        return min(possible_dates)

    def date_for_country(self, days: int, country: Country) -> dt.date:
        calendar = ExtendedCalendar(
            type(self).BANK_HOLIDAY_CALENDAR.from_country(country),
            rules=[ChristmasEveRule()],
            years=[self.poll_date.year - 1, self.poll_date.year],
        )

        return working_days_before(self.poll_date, days, calendar)
