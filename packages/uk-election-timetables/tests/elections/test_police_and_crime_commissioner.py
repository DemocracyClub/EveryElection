import datetime as dt

from uk_election_timetables.elections import PoliceAndCrimeCommissionerElection


# Reference election: pcc.avon-and-somerset.2016-05-05
def test_publish_date_police_and_crime_commissioner():
    election = PoliceAndCrimeCommissionerElection(dt.date(2016, 5, 5))

    assert election.sopn_publish_date == dt.date(2016, 4, 8)


# Reference election: pcc.2021-05-06
def test_registration_deadline_police_and_crime_commissioner():
    election = PoliceAndCrimeCommissionerElection(dt.date(2021, 5, 6))

    assert election.registration_deadline == dt.date(2021, 4, 19)


# Reference election: pcc.2021-05-06
def test_postal_vote_application_deadline_police_and_crime_commissioner():
    election = PoliceAndCrimeCommissionerElection(dt.date(2021, 5, 6))

    assert election.postal_vote_application_deadline == dt.date(2021, 4, 20)


# Reference election: pcc.2026-05-07
def test_notice_of_election_deadline():
    election = PoliceAndCrimeCommissionerElection(dt.date(2024, 5, 2))

    assert election.notice_of_election_deadline == dt.date(2024, 3, 26)
