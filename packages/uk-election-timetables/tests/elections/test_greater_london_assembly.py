import datetime as dt

from uk_election_timetables.elections import GreaterLondonAssemblyElection


# Reference election: gla.c.barnet-and-camden.2016-05-05
def test_publish_date_greater_london_assembly():
    publish_date = GreaterLondonAssemblyElection(
        dt.date(2016, 5, 5)
    ).sopn_publish_date

    assert publish_date == dt.date(2016, 4, 4)


# Reference election: mayor.london.2016-05-05
def test_publish_date_mayor_london():
    publish_date = GreaterLondonAssemblyElection(
        dt.date(2016, 5, 5)
    ).sopn_publish_date

    assert publish_date == dt.date(2016, 4, 4)


# Reference election: gla.2021-05-06
def test_registration_deadline_london_assembly():
    election = GreaterLondonAssemblyElection(dt.date(2021, 5, 6))

    assert election.registration_deadline == dt.date(2021, 4, 19)


# Reference election: gla.2024-05-02
def test_notice_of_election_deadline():
    election = GreaterLondonAssemblyElection(dt.date(2024, 5, 2))

    assert election.notice_of_election_deadline == dt.date(2024, 3, 19)
