from datetime import date

from pytest import raises

from uk_election_timetables.calendars import Country
from uk_election_timetables.election_ids import (
    AmbiguousElectionIdError,
    InvalidElectionIdError,
    NoSuchElectionTypeError,
    from_election_id,
)
from uk_election_timetables.elections import (
    NorthernIrelandAssemblyElection,
    PoliceAndCrimeCommissionerElection,
    ScottishParliamentElection,
    SeneddCymruElection,
    UKParliamentElection,
)


def test_publish_date_local_id():
    with raises(AmbiguousElectionIdError) as err:
        from_election_id("local.2019-02-21")

    assert (
        str(err.value)
        == "Cannot derive country from election id [local.2019-02-21]"
    )


def test_publish_date_local_id_with_country():
    election = from_election_id("local.2019-02-21", country=Country.ENGLAND)

    assert election.sopn_publish_date == date(2019, 1, 25)


def test_publish_date_parl_id_with_country():
    election = from_election_id("parl.2019-02-21", country=Country.ENGLAND)

    assert election.sopn_publish_date == date(2019, 1, 25)


def test_publish_date_parl_id_without_country():
    election = from_election_id("parl.2019-02-21")

    assert election.sopn_publish_date == date(2019, 1, 25)


def test_publish_date_not_an_election_type():
    with raises(NoSuchElectionTypeError) as err:
        from_election_id("not-an-election.2019-02-21")

    assert str(err.value) == "Election type [not-an-election] does not exist"


def test_publish_date_id_that_does_not_need_country():
    election = from_election_id("naw.c.ceredigion.2016-05-05")

    assert election.sopn_publish_date == date(2016, 4, 7)


def test_publish_date_invalid_id():
    with raises(InvalidElectionIdError) as err:
        from_election_id("not an election id")

    assert (
        str(err.value)
        == "Parameter [not an election id] is not in election id format"
    )


def test_publish_date_invalid_date():
    with raises(InvalidElectionIdError) as err:
        from_election_id("parl.not-a-date")

    assert (
        str(err.value)
        == "Parameter [parl.not-a-date] is not in election id format"
    )


def test_publish_date_senedd_election_id():
    election = from_election_id("senedd.c.ceredigion.2016-05-05")

    assert election.sopn_publish_date == date(2016, 4, 7)


def test_christmas_eve_not_counted():
    election_and_expected_sopn_date = {
        PoliceAndCrimeCommissionerElection: date(2018, 12, 11),
        UKParliamentElection: date(2018, 12, 7),
        ScottishParliamentElection: date(2018, 12, 3),
        NorthernIrelandAssemblyElection: date(2018, 12, 13),
        SeneddCymruElection: date(2018, 12, 10),
    }

    for election_on, expected_date in election_and_expected_sopn_date.items():
        assert election_on(date(2019, 1, 10)).sopn_publish_date == expected_date
