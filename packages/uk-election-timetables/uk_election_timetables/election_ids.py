from datetime import datetime, date

from uk_election_timetables.calendars import Country

from uk_election_timetables.election import Election

from uk_election_timetables.elections import (
    NorthernIrelandAssemblyElection,
    ScottishParliamentElection,
    SeneddCymruElection,
    GreaterLondonAssemblyElection,
    PoliceAndCrimeCommissionerElection,
    MayoralElection,
    LocalElection,
    UKParliamentElection,
)


class InvalidElectionIdError(BaseException):
    """
    An exception type to represent when an election id does not confirm to DemocracyClub's `uk-election-ids <https://elections.democracyclub.org.uk/reference_definition/>`_ format
    """

    def __init__(self, election_id: str):
        self.election_id = election_id

    def __str__(self):
        return "Parameter [%s] is not in election id format" % self.election_id


class NoSuchElectionTypeError(BaseException):
    """
    An exception type to represent when an election type doesn't actually represent a valid election.
    """

    def __init__(self, election_type: str):
        self.election_type = election_type

    def __str__(self):
        return "Election type [%s] does not exist" % self.election_type


class AmbiguousElectionIdError(BaseException):
    """
    An exception type to represent when an election id (usually a group such as `local.2019-05-02`) can correspond to elections in multiple countries with different legislation governing the publish date of Statements of Persons Nominated.
    """

    def __init__(self, election_id: str):
        self.election_id = election_id

    def __str__(self):
        return "Cannot derive country from election id [%s]" % self.election_id


def type_and_poll_date(election_id: str) -> (str, date):
    """
    Extract election_type (e.g. parl, local, mayor) and poll_date from an election id.

    :param election_id: a string representing an election id in `uk-election-ids <https://elections.democracyclub.org.uk/reference_definition/>`_ format
    :return: a tuple (election_type: str, poll_date: date)
    """
    try:
        election_type, *_, poll_date = election_id.split(".")

        date_of_poll = datetime.strptime(poll_date, "%Y-%m-%d").date()

        return election_type, date_of_poll
    except Exception:
        raise InvalidElectionIdError(election_id)


def from_election_id(election_id: str, country: Country = None) -> Election:
    """
    Calculate the publish date for an election given in `uk-election-ids <https://elections.democracyclub.org.uk/reference_definition/>`_ format and an optional country if necessary (for example, local or parliamentary elections).

    :param election_id: a string representing an election id in uk-election-ids format
    :param country: an optional Country representing the country where the election will be held
    :return: a datetime representing the expected publish date
    """
    election_id_lookup = {
        "nia": NorthernIrelandAssemblyElection,
        "sp": ScottishParliamentElection,
        "naw": SeneddCymruElection,
        "senedd": SeneddCymruElection,
        "gla": GreaterLondonAssemblyElection,
        "pcc": PoliceAndCrimeCommissionerElection,
        "mayor": MayoralElection,
    }

    election_type, poll_date = type_and_poll_date(election_id)

    def valid_election_type(el_type):
        return el_type in election_id_lookup or el_type in [
            "local",
            "parl",
        ]

    def requires_country(el_type):
        return el_type in ["local"]

    if not valid_election_type(election_type):
        raise NoSuchElectionTypeError(election_type)

    if requires_country(election_type) and country is None:
        raise AmbiguousElectionIdError(election_id)

    if election_type in election_id_lookup:
        return election_id_lookup[election_type](poll_date)

    if election_type == "local":
        return LocalElection(poll_date, country)
    elif election_type == "parl":
        return UKParliamentElection(poll_date, country)
