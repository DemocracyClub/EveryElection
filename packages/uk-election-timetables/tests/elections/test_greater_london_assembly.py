from datetime import date
from uk_election_timetables.elections import GreaterLondonAssemblyElection


# Reference election: gla.c.barnet-and-camden.2016-05-05
def test_publish_date_greater_london_assembly():
    publish_date = GreaterLondonAssemblyElection(date(2016, 5, 5)).sopn_publish_date

    assert publish_date == date(2016, 4, 1)


# Reference election: mayor.london.2016-05-05
def test_publish_date_mayor_london():
    publish_date = GreaterLondonAssemblyElection(date(2016, 5, 5)).sopn_publish_date

    assert publish_date == date(2016, 4, 1)
