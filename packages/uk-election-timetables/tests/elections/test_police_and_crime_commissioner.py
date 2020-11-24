from datetime import date

from uk_election_timetables.elections import PoliceAndCrimeCommissionerElection


# Reference election: pcc.avon-and-somerset.2016-05-05
def test_publish_date_police_and_crime_commissioner():
    election = PoliceAndCrimeCommissionerElection(date(2016, 5, 5))

    assert election.sopn_publish_date == date(2016, 4, 8)
