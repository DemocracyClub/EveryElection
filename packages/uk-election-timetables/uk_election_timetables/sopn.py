from uk_election_timetables.calendars import (
    UnitedKingdomBankHolidays,
    Country,
    Region,
    working_days_before,
    FixedDates,
)
from uk_election_timetables.election_ids import (
    type_and_poll_date,
    AmbiguousElectionIdError,
    NoSuchElectionTypeError,
)

from warnings import warn
from datetime import date


class StatementPublishDate(object):
    def __init__(self):
        self.election_id_lookup = {
            "nia": self.northern_ireland_assembly,
            "sp": self.scottish_parliament,
            "naw": self.senedd_cymru,
            "senedd": self.senedd_cymru,
            "gla": self.greater_london_assembly,
            "pcc": self.police_and_crime_commissioner,
            "mayor": self.mayor,
        }
        self.calendar = UnitedKingdomBankHolidays()

    def for_id(self, election_id: str, country: Country = None) -> date:
        """
        Calculate the publish date for an election given in `uk-election-ids <https://elections.democracyclub.org.uk/reference_definition/>`_ format and an optional country if necessary (for example, local or parliamentary elections).

        This function returns *None* for elections to the European Parliament, and will raise an exception if the election id is ambiguous (could correspond to elections in multiple countries with different electoral legislation).

        :param election_id: a string representing an election id in uk-election-ids format
        :param country: an optional Country representing the country where the election will be held
        :return: a datetime representing the expected publish date
        """

        election_type, poll_date = type_and_poll_date(election_id)

        def valid_election_type(el_type):
            return el_type in self.election_id_lookup or el_type in [
                "local",
                "parl",
                "europarl",
            ]

        def requires_country(el_type):
            return el_type in ["local", "europarl"]

        if not valid_election_type(election_type):
            raise NoSuchElectionTypeError(election_type)

        if requires_country(election_type) and country is None:
            raise AmbiguousElectionIdError(election_id)

        if election_type in self.election_id_lookup:
            return self.election_id_lookup[election_type](poll_date)

        if election_type == "local":
            return self.local(poll_date, country=country)
        elif election_type == "parl":
            return self.uk_parliament(poll_date, country=country)
        elif election_type == "europarl":
            return None

    def northern_ireland_assembly(self, poll_date: date) -> date:
        """
        Calculate the publish date for an election to the Northern Ireland Assembly

        This is set out by Schedule 5, Rules 1 and 2 of `The Northern Ireland Assembly (Elections) (Amendment) Order 2009 <https://www.legislation.gov.uk/uksi/2009/256/made>`_

        :param poll_date: a datetime representing the date of the poll
        :return: a datetime representing the expected publish date
        """
        return working_days_before(poll_date, 16, self.calendar.northern_ireland())

    def scottish_parliament(self, poll_date: date) -> date:
        """
        Calculate the publish date for an election to the Scottish Parliament

        This is set out in `The Scottish Parliament (Elections etc.) Order 2015 <https://www.legislation.gov.uk/ssi/2015/425/made>`_

        :param poll_date: a datetime representing the date of the poll
        :return: a datetime representing the expected publish date
        """
        return working_days_before(poll_date, 23, self.calendar.scotland())

    def national_assembly_for_wales(self, poll_date: date) -> date:
        """
        Calculate the publish date for an election to the National Assembly for Wales

        This is set out in `The National Assembly for Wales (Representation of the People) (Amendment) Order 2016 <https://www.legislation.gov.uk/uksi/2016/272/article/18/made>`_

        :param poll_date: a datetime representing the date of the poll
        :return: a datetime representing the expected publish date
        """
        warn(
            "national_assembly_for_wales is deprecated, use senedd_cymru instead",
            DeprecationWarning,
        )

        return working_days_before(poll_date, 19, self.calendar.england_and_wales())

    def senedd_cymru(self, poll_date: date) -> date:
        """
        Calculate the publish date for an election to the Senedd Cymru / Welsh Parliament

        This is set out in `Senedd and Elections (Wales) Act 2020 <https://www.legislation.gov.uk/anaw/2020/1/contents>` and `The National Assembly for Wales (Representation of the People) (Amendment) Order 2016 <https://www.legislation.gov.uk/uksi/2016/272/article/18/made>`_

        :param poll_date: a datetime representing the date of the poll
        :return: a datetime representing the expected publish date
        """
        return working_days_before(poll_date, 19, self.calendar.england_and_wales())

    def greater_london_assembly(self, poll_date: date) -> date:
        """
        Calculate the publish date for an election to the Greater London Assembly

        This is set out in `The Greater London Authority Elections (Amendment) Rules 2016 <https://www.legislation.gov.uk/uksi/2016/24/article/6/made>`_

        :param poll_date: a datetime representing the date of the poll
        :return: a datetime representing the expected publish date
        """
        return working_days_before(poll_date, 23, self.calendar.england_and_wales())

    def european_parliament(self, poll_date: date, region: Region) -> date:
        """
        Calculate the publish date for an election to the European Parliament

        This is set out in `The European Parliamentary Elections (Amendment) Regulations 2009 <https://www.legislation.gov.uk/uksi/2009/186/made>`_

        As Gibraltar is included within *South West England* but has a different bank holiday calendar, it's plausible that the SoPN date for *South West England* will differ from the rest of England.

        :param poll_date: a datetime representing the date of the poll
        :param region: the region of the UK and Gibraltar where the poll is being run
        :return: a datetime representing the expected publish date
        """

        def date_with_calendar(calendar):
            return working_days_before(poll_date, 19, calendar)

        if region == Region.SCOTLAND:
            return date_with_calendar(self.calendar.scotland())
        elif region == Region.NORTHERN_IRELAND:
            return date_with_calendar(self.calendar.northern_ireland())
        elif region == Region.SOUTH_WEST_ENGLAND:
            return min(
                date_with_calendar(self.calendar.england_and_wales()),
                FixedDates.EUROPARL_GIBRALTAR_2019,
            )
        else:
            return date_with_calendar(self.calendar.england_and_wales())

    def police_and_crime_commissioner(self, poll_date: date) -> date:
        """
        Calculate the publish date for an election to the position of Police and Crime Commissioner

        This is set out in `The Police and Crime Commissioner Elections (Amendment) Order 2014 <https://www.legislation.gov.uk/uksi/2014/921/article/31/made>`_

        :param poll_date: a datetime representing the date of the poll
        :return: a datetime representing the expected publish date
        """
        return working_days_before(poll_date, 18, self.calendar.england_and_wales())

    def mayor(self, poll_date: date) -> date:
        """
        Calculate the publish date for an election to the position of Mayor in England and Wales

        This is set out in `The Local Authorities (Mayoral Elections) (England and Wales) (Amendment) Regulations 2014 <https://www.legislation.gov.uk/uksi/2014/370/made>`_

        :param poll_date: a datetime representing the date of the poll
        :return: a datetime representing the expected publish date
        """
        return working_days_before(poll_date, 19, self.calendar.england_and_wales())

    def uk_parliament(self, poll_date: date, country: Country = None):
        """
        Calculate the publish date for an election to the Parliament of the United Kingdom

        This is set out in `Representation of the People Act 1983 <https://www.legislation.gov.uk/ukpga/1983/2/contents>`_ and its amendments.

        :param poll_date: a datetime representing the date of the poll
        :param country: an optional Country representing the country where the election will be held
        :return: a datetime representing the expected publish date
        """

        def date_for_country(country_of_election: Country) -> date:
            calendar = self.calendar.from_country(country_of_election)
            return working_days_before(poll_date, 19, calendar)

        if country:
            return date_for_country(country)

        else:
            possible_dates = [
                date_for_country(country)
                for country in [
                    Country.ENGLAND,
                    Country.SCOTLAND,
                    Country.NORTHERN_IRELAND,
                ]
            ]

            return min(possible_dates)

    def local(self, poll_date: date, country: Country):
        """
        Calculate the publish date for a local election.

        This is set out in:

         * `The Local Elections (Principal Areas) (England and Wales) (Amendment) Rules 2014 <https://www.legislation.gov.uk/uksi/2014/494/made>`_
         * `The Local Elections (Northern Ireland) Order 2010 <https://www.legislation.gov.uk/uksi/2010/2977/schedule/1/part/4/made>`_
         * `The Scottish Local Government Elections Order 2011 <https://www.legislation.gov.uk/ssi/2011/399/made>`_

        :param poll_date: a datetime representing the date of the poll
        :param country: the country in which the election is being run
        :return: a datetime representing the expected publish date
        """

        country_specific_duration = {
            Country.ENGLAND: 18,
            Country.NORTHERN_IRELAND: 16,
            Country.SCOTLAND: 23,
            Country.WALES: 18,
        }

        days_prior = country_specific_duration[country]

        return working_days_before(
            poll_date, days_prior, self.calendar.from_country(country)
        )
