import datetime as dt

from uk_election_timetables.elections import NorthernIrelandAssemblyElection


# Reference election: nia.belfast-east.2017-03-02
def test_publish_date_northern_ireland_assembly():
    publish_date = NorthernIrelandAssemblyElection(
        dt.date(2017, 3, 2)
    ).close_of_nominations

    assert publish_date == dt.date(2017, 2, 8)


# Reference election: nia.2022-05-05
def test_notice_of_election_deadline():
    election = NorthernIrelandAssemblyElection(dt.date(2022, 5, 5))

    assert election.notice_of_election_deadline == dt.date(2022, 3, 28)


def test_registration_deadline():
    """
    note: this test is just reverse-engineered from the code

    There were no NIA elections in Northern Ireland in 2026

    Replace it with a test based on a real-world example
    when we have one to hand (TODO: 2027)
    """
    election = NorthernIrelandAssemblyElection(dt.date(2026, 5, 7))

    assert election.registration_deadline == dt.date(2026, 4, 20)


def test_postal_vote_application_deadline():
    """
    note: this test is just reverse-engineered from the code

    There were no NIA elections in Northern Ireland in 2026

    Replace it with a test based on a real-world example
    when we have one to hand (TODO: 2027)
    """
    election = NorthernIrelandAssemblyElection(dt.date(2026, 5, 7))

    assert election.postal_vote_application_deadline == dt.date(2026, 4, 16)


def test_proxy_vote_application_deadline():
    """
    note: this test is just reverse-engineered from the code

    There were no NIA elections in Northern Ireland in 2026

    Replace it with a test based on a real-world example
    when we have one to hand (TODO: 2027)
    """
    election = NorthernIrelandAssemblyElection(dt.date(2026, 5, 7))

    assert election.proxy_vote_application_deadline == dt.date(2026, 4, 16)
