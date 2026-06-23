import datetime as dt

from uk_election_timetables.elections import NorthernIrelandAssemblyElection


# Reference election: nia.belfast-east.2017-03-02
def test_publish_date_northern_ireland_assembly():
    publish_date = NorthernIrelandAssemblyElection(
        dt.date(2017, 3, 2)
    ).sopn_publish_date

    assert publish_date == dt.date(2017, 2, 8)


# Reference election: nia.2022-05-05
def test_notice_of_election_deadline():
    election = NorthernIrelandAssemblyElection(dt.date(2022, 5, 5))

    assert election.notice_of_election_deadline == dt.date(2022, 3, 28)
