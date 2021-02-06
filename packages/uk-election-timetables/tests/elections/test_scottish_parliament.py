from datetime import date

from uk_election_timetables.elections import (
    ScottishParliamentElection,
)


# Reference election: sp.c.shetland-islands.2016-05-05
def test_publish_date_scottish_parliament():
    publish_date = ScottishParliamentElection(date(2016, 5, 5)).sopn_publish_date

    assert publish_date == date(2016, 4, 1)


# Reference election: sp.2021-05-06
def test_registration_deadline_scottish_parliament():
    election = ScottishParliamentElection(date(2021, 5, 6))

    assert election.registration_deadline == date(2021, 4, 19)
