from datetime import date

from uk_election_timetables.elections import SeneddCymruElection


# Reference election: naw.c.ceredigion.2016-05-05
def test_publish_date_senedd_cymru():
    publish_date = SeneddCymruElection(date(2016, 5, 5)).sopn_publish_date

    assert publish_date == date(2016, 4, 7)


# Reference election: senedd.2021-05-06
def test_registration_deadline_senedd_cymru():
    election = SeneddCymruElection(date(2021, 5, 6))

    assert election.registration_deadline == date(2021, 4, 19)
