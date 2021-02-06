from datetime import date

from uk_election_timetables.elections import MayoralElection


# Reference election: mayor.liverpool-city-ca.2017-05-04
def test_publish_date_mayor():
    election = MayoralElection(date(2017, 5, 4))

    assert election.sopn_publish_date == date(2017, 4, 4)


# Reference election: mayor.2021-05-06
def test_registration_deadline_mayor():
    election = MayoralElection(date(2021, 5, 6))

    assert election.registration_deadline == date(2021, 4, 19)
