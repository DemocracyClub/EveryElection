from datetime import datetime, date


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
