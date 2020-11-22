from datetime import date

from uk_election_timetables.elections import MayoralElection


# Reference election: mayor.liverpool-city-ca.2017-05-04
def test_publish_date_mayor():
    election = MayoralElection(date(2017, 5, 4))

    assert election.sopn_publish_date() == date(2017, 4, 4)
