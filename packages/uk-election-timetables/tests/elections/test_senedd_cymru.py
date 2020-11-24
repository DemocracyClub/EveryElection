from datetime import date

from uk_election_timetables.elections import SeneddCymruElection


# Reference election: naw.c.ceredigion.2016-05-05
def test_publish_date_senedd_cymru():
    publish_date = SeneddCymruElection(date(2016, 5, 5)).sopn_publish_date

    assert publish_date == date(2016, 4, 7)
