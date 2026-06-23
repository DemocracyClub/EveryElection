import datetime as dt

from uk_election_timetables.elections import SeneddCymruElection


# Reference election: naw.c.ceredigion.2016-05-05
def test_publish_date_senedd_cymru():
    publish_date = SeneddCymruElection(dt.date(2016, 5, 5)).sopn_publish_date

    assert publish_date == dt.date(2016, 4, 7)


# Reference election: senedd.2021-05-06
def test_registration_deadline_senedd_cymru():
    election = SeneddCymruElection(dt.date(2021, 5, 6))

    assert election.registration_deadline == dt.date(2021, 4, 19)


# Reference election: senedd.2021-05-06
def test_postal_vote_application_deadline_senedd_cymru():
    election = SeneddCymruElection(dt.date(2021, 5, 6))

    assert election.postal_vote_application_deadline == dt.date(2021, 4, 20)


# Reference election: senedd.2026-05-07
def test_notice_of_election_deadline():
    election = SeneddCymruElection(dt.date(2026, 5, 7))

    assert election.notice_of_election_deadline == dt.date(2026, 3, 30)
