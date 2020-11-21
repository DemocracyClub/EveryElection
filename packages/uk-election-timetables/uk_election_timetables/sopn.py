from uk_election_timetables.calendars import (
    UnitedKingdomBankHolidays,
    Country,
    working_days_before,
)
from uk_election_timetables.election_ids import (
    type_and_poll_date,
    AmbiguousElectionIdError,
    NoSuchElectionTypeError,
)

from warnings import warn
from datetime import date

from uk_election_timetables.elections import (
    ScottishParliamentElection,
    SeneddCymruElection,
    GreaterLondonAssemblyElection,
    NorthernIrelandAssemblyElection,
    LocalElection,
    UKParliamentElection,
)


class StatementPublishDate(object):
    def __init__(self):
        self.election_id_lookup = {
            "nia": lambda x: NorthernIrelandAssemblyElection(x).sopn_publish_date(),
            "sp": lambda x: ScottishParliamentElection(x).sopn_publish_date(),
            "naw": lambda x: SeneddCymruElection(x).sopn_publish_date(),
            "senedd": lambda x: SeneddCymruElection(x).sopn_publish_date(),
            "gla": lambda x: GreaterLondonAssemblyElection(x).sopn_publish_date(),
            "pcc": self.police_and_crime_commissioner,
            "mayor": self.mayor,
        }
        self.calendar = UnitedKingdomBankHolidays()

    def for_id(self, election_id: str, country: Country = None) -> date:
        """
        Calculate the publish date for an election given in `uk-election-ids <https://elections.democracyclub.org.uk/reference_definition/>`_ format and an optional country if necessary (for example, local or parliamentary elections).

        :param election_id: a string representing an election id in uk-election-ids format
        :param country: an optional Country representing the country where the election will be held
        :return: a datetime representing the expected publish date
        """

        election_type, poll_date = type_and_poll_date(election_id)

        def valid_election_type(el_type):
            return el_type in self.election_id_lookup or el_type in [
                "local",
                "parl",
            ]

        def requires_country(el_type):
            return el_type in ["local"]

        if not valid_election_type(election_type):
            raise NoSuchElectionTypeError(election_type)

        if requires_country(election_type) and country is None:
            raise AmbiguousElectionIdError(election_id)

        if election_type in self.election_id_lookup:
            return self.election_id_lookup[election_type](poll_date)

        if election_type == "local":
            return LocalElection(poll_date, country).sopn_publish_date()
        elif election_type == "parl":
            return UKParliamentElection(poll_date, country).sopn_publish_date()

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
