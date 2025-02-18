import datetime
from typing import Dict

import pytest

from uk_election_timetables import elections
from uk_election_timetables.calendars import Country
from uk_election_timetables.election import Election, TimetableEvent
from uk_election_timetables.election_ids import from_election_id


def test_timetable_sopn_publish_date():
    election = from_election_id("parl.2019-02-21", country=Country.ENGLAND)

    sopn_publish_date = lookup(election, "List of candidates published")

    assert sopn_publish_date["date"] == datetime.date(2019, 1, 25)


def test_timetable_registration_deadline():
    election = from_election_id("local.2021-05-06", country=Country.ENGLAND)

    electoral_registration_deadline = lookup(
        election, "Register to vote deadline"
    )

    assert electoral_registration_deadline["date"] == datetime.date(2021, 4, 19)


def test_timetable_postal_vote_application_deadline():
    election = from_election_id("local.2021-05-06", country=Country.ENGLAND)

    postal_vote_dealine = lookup(election, "Postal vote application deadline")

    assert postal_vote_dealine["date"] == datetime.date(2021, 4, 20)


def test_timetable_vac_application_deadline():
    election = from_election_id("parl.2023-05-04", country=Country.ENGLAND)

    vac_deadline = lookup(election, "VAC application deadline")

    assert vac_deadline["date"] == datetime.date(2023, 4, 25)


def test_timetable_sort_order():
    election = from_election_id("local.2021-05-06", country=Country.ENGLAND)

    assert len(election.timetable) == 4

    assert election.timetable == [
        {
            "label": "List of candidates published",
            "date": datetime.date(2021, 4, 9),
            "event": "SOPN_PUBLISH_DATE",
        },
        {
            "label": "Register to vote deadline",
            "date": datetime.date(2021, 4, 19),
            "event": "REGISTRATION_DEADLINE",
        },
        {
            "label": "Postal vote application deadline",
            "date": datetime.date(2021, 4, 20),
            "event": "POSTAL_VOTE_APPLICATION_DEADLINE",
        },
        {
            "label": "VAC application deadline",
            "date": datetime.date(2021, 4, 27),
            "event": "VAC_APPLICATION_DEADLINE",
        },
    ]


def test_timetable_sort_order_scottish_parliament_postal_vote():
    election = from_election_id("sp.c.2021-05-06")

    assert len(election.timetable) == 4

    assert election.timetable == [
        {
            "label": "List of candidates published",
            "date": datetime.date(2021, 4, 1),
            "event": "SOPN_PUBLISH_DATE",
        },
        {
            "label": "Postal vote application deadline",
            "date": datetime.date(2021, 4, 6),
            "event": "POSTAL_VOTE_APPLICATION_DEADLINE",
        },
        {
            "label": "Register to vote deadline",
            "date": datetime.date(2021, 4, 19),
            "event": "REGISTRATION_DEADLINE",
        },
        {
            "label": "VAC application deadline",
            "date": datetime.date(2021, 4, 27),
            "event": "VAC_APPLICATION_DEADLINE",
        },
    ]


def lookup(election: Election, label: str) -> Dict:
    return next(
        entry for entry in election.timetable if entry["label"] == label
    )


def test_get_date_for_event_type():
    election = from_election_id("parl.2019-02-21", country=Country.ENGLAND)
    assert election.get_date_for_event_type(
        TimetableEvent("List of candidates published")
    ) == datetime.date(2019, 1, 25)
    assert election.get_date_for_event_type(
        TimetableEvent("Postal vote application deadline")
    ) == datetime.date(2019, 2, 6)
    assert election.get_date_for_event_type(
        TimetableEvent("Register to vote deadline")
    ) == datetime.date(2019, 2, 5)
    assert election.get_date_for_event_type(
        TimetableEvent("VAC application deadline")
    ) == datetime.date(2019, 2, 13)


def test_event_type_enum():
    assert (
        TimetableEvent.REGISTRATION_DEADLINE.value
        == "Register to vote deadline"
    )
    assert (
        TimetableEvent.SOPN_PUBLISH_DATE.value == "List of candidates published"
    )
    assert (
        TimetableEvent.POSTAL_VOTE_APPLICATION_DEADLINE.value
        == "Postal vote application deadline"
    )
    assert (
        TimetableEvent.VAC_APPLICATION_DEADLINE.value
        == "VAC application deadline"
    )


def test_is_before():
    election = from_election_id("parl.2019-02-21", country=Country.ENGLAND)
    assert election.is_before(TimetableEvent.REGISTRATION_DEADLINE) is False
    assert election.is_before(TimetableEvent.SOPN_PUBLISH_DATE) is False
    assert (
        election.is_before(TimetableEvent.POSTAL_VOTE_APPLICATION_DEADLINE)
        is False
    )
    assert election.is_before(TimetableEvent.VAC_APPLICATION_DEADLINE) is False


def test_is_after():
    election = from_election_id("parl.2019-02-21", country=Country.ENGLAND)
    assert election.is_after(TimetableEvent.REGISTRATION_DEADLINE) is True
    assert election.is_after(TimetableEvent.SOPN_PUBLISH_DATE) is True
    assert (
        election.is_after(TimetableEvent.POSTAL_VOTE_APPLICATION_DEADLINE)
        is True
    )
    assert election.is_after(TimetableEvent.VAC_APPLICATION_DEADLINE) is True


election_types = [
    {
        "election_id": "nia.2019-02-21",
        "country": None,
        "expected_type": elections.NorthernIrelandAssemblyElection,
    },
    {
        "election_id": "naw.2019-02-21",
        "country": None,
        "expected_type": elections.SeneddCymruElection,
    },
    {
        "election_id": "senedd.2019-02-21",
        "country": None,
        "expected_type": elections.SeneddCymruElection,
    },
    {
        "election_id": "gla.2019-02-21",
        "country": None,
        "expected_type": elections.GreaterLondonAssemblyElection,
    },
    {
        "election_id": "pcc.2019-02-21",
        "country": None,
        "expected_type": elections.PoliceAndCrimeCommissionerElection,
    },
    {
        "election_id": "mayor.doncaster.2019-02-21",
        "country": None,
        "expected_type": elections.MayoralElection,
    },
    {
        "election_id": "mayor.london.2019-02-21",
        "country": None,
        "expected_type": elections.GreaterLondonAssemblyElection,
    },
    # City of London
    {
        "election_id": "local.city-of-london.2019-02-21",  # Common Council
        "country": None,
        "expected_type": elections.CityOfLondonLocalElection,
    },
    {
        "election_id": "local.city-of-london-alder.2019-02-21",  # Aldermen
        "country": None,
        "expected_type": elections.CityOfLondonLocalElection,
    },
    # local
    {
        "election_id": "local.somewhere.2019-02-21",
        "country": Country.ENGLAND,
        "expected_type": elections.LocalElection,
    },
    {
        "election_id": "local.somewhere.2019-02-21",
        "country": Country.WALES,
        "expected_type": elections.LocalElection,
    },
    # parl
    {
        "election_id": "parl.somewhere.2019-02-21",
        "country": Country.ENGLAND,
        "expected_type": elections.UKParliamentElection,
    },
    {
        "election_id": "parl.somewhere.2019-02-21",
        "country": Country.WALES,
        "expected_type": elections.UKParliamentElection,
    },
]


@pytest.mark.parametrize("election", election_types)
def test_from_election_types_types(election):
    assert isinstance(
        from_election_id(election["election_id"], election["country"]),
        election["expected_type"],
    )


def test_city_of_london_does_not_mutate_global_calendar():
    assert from_election_id(
        "mayor.doncaster.2025-05-01", Country.ENGLAND
    ).sopn_publish_date == datetime.date(2025, 4, 2)

    assert from_election_id(
        "local.city-of-london.aldersgate.2025-03-20", Country.ENGLAND
    ).sopn_publish_date == datetime.date(2025, 2, 26)

    # calculating the date for a City of London election
    # shouldn't change this result
    assert from_election_id(
        "mayor.doncaster.2025-05-01", Country.ENGLAND
    ).sopn_publish_date == datetime.date(2025, 4, 2)
