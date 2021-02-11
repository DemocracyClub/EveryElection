from datetime import date
from typing import Dict

from uk_election_timetables.calendars import Country
from uk_election_timetables.election import Election
from uk_election_timetables.election_ids import from_election_id


def test_timetable_sopn_publish_date():
    election = from_election_id("parl.2019-02-21", country=Country.ENGLAND)

    sopn_publish_date = lookup(election, "List of candidates published")

    assert sopn_publish_date["date"] == date(2019, 1, 25)


def test_timetable_registration_deadline():
    election = from_election_id("local.2021-05-06", country=Country.ENGLAND)

    sopn_publish_date = lookup(election, "Register to vote deadline")

    assert sopn_publish_date["date"] == date(2021, 4, 19)


def test_timetable_sort_order():
    election = from_election_id("local.2021-05-06", country=Country.ENGLAND)
    assert len(election.timetable) == 2
    assert [r["date"] for r in election.timetable] == [
        date(2021, 4, 9),
        date(2021, 4, 19),
    ]


def lookup(election: Election, label: str) -> Dict:
    return next(entry for entry in election.timetable if entry["label"] == label)
