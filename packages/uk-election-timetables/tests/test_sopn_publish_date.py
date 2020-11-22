from uk_election_timetables.elections import (
    ScottishParliamentElection,
    SeneddCymruElection,
    NorthernIrelandAssemblyElection,
    UKParliamentElection,
    PoliceAndCrimeCommissionerElection,
)

from uk_election_timetables.sopn import StatementPublishDate
from uk_election_timetables.calendars import Country
from uk_election_timetables.election_ids import (
    InvalidElectionIdError,
    AmbiguousElectionIdError,
    NoSuchElectionTypeError,
)

from datetime import date
from pytest import raises
from warnings import catch_warnings

sopn_publish_date = StatementPublishDate()


def test_publish_date_local_id():

    with raises(AmbiguousElectionIdError) as err:
        sopn_publish_date.for_id("local.2019-02-21")

    assert str(err.value) == "Cannot derive country from election id [local.2019-02-21]"


def test_publish_date_local_id_with_country():
    publish_date = sopn_publish_date.for_id("local.2019-02-21", country=Country.ENGLAND)

    assert publish_date == date(2019, 1, 28)


def test_publish_date_parl_id_with_country():
    publish_date = sopn_publish_date.for_id("parl.2019-02-21", country=Country.ENGLAND)

    assert publish_date == date(2019, 1, 25)


def test_publish_date_parl_id_without_country():
    publish_date = sopn_publish_date.for_id("parl.2019-02-21")

    assert publish_date == date(2019, 1, 25)


def test_publish_date_not_an_election_type():

    with raises(NoSuchElectionTypeError) as err:
        sopn_publish_date.for_id("not-an-election.2019-02-21")

    assert str(err.value) == "Election type [not-an-election] does not exist"


def test_publish_date_id_that_does_not_need_country():
    publish_date = sopn_publish_date.for_id("naw.c.ceredigion.2016-05-05")

    assert publish_date == date(2016, 4, 7)


def test_publish_date_invalid_id():

    with raises(InvalidElectionIdError) as err:
        sopn_publish_date.for_id("not an election id")

    assert (
        str(err.value) == "Parameter [not an election id] is not in election id format"
    )


def test_publish_date_invalid_date():

    with raises(InvalidElectionIdError) as err:
        sopn_publish_date.for_id("parl.not-a-date")

    assert str(err.value) == "Parameter [parl.not-a-date] is not in election id format"


def test_publish_date_senedd_election_id():
    publish_date = sopn_publish_date.for_id("senedd.c.ceredigion.2016-05-05")

    assert publish_date == date(2016, 4, 7)


# Reference election: mayor.liverpool-city-ca.2017-05-04
def test_publish_date_mayor():
    publish_date = sopn_publish_date.mayor(date(2017, 5, 4))

    assert publish_date == date(2017, 4, 4)


def test_national_assembly_for_wales_deprecation_warning():
    with catch_warnings(record=True) as warnings:
        sopn_publish_date.national_assembly_for_wales(date(2020, 1, 1))

        assert len(warnings) == 1

        warning = warnings[-1]

        assert issubclass(warning.category, DeprecationWarning)
        assert (
            str(warning.message)
            == "national_assembly_for_wales is deprecated, use senedd_cymru instead"
        )


def test_christmas_eve_not_counted():

    election_and_expected_sopn_date = {
        lambda x: PoliceAndCrimeCommissionerElection(x).sopn_publish_date(): date(
            2018, 12, 11
        ),
        lambda x: UKParliamentElection(x).sopn_publish_date(): date(2018, 12, 7),
        lambda x: ScottishParliamentElection(x).sopn_publish_date(): date(2018, 12, 3),
        lambda x: NorthernIrelandAssemblyElection(x).sopn_publish_date(): date(
            2018, 12, 13
        ),
        lambda x: SeneddCymruElection(x).sopn_publish_date(): date(2018, 12, 10),
    }

    for sopn_for_election_on, expected_date in election_and_expected_sopn_date.items():
        assert sopn_for_election_on(date(2019, 1, 10)) == expected_date
