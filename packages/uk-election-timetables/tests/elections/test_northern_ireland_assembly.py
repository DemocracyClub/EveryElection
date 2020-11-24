from datetime import date
from uk_election_timetables.elections import NorthernIrelandAssemblyElection


# Reference election: nia.belfast-east.2017-03-02
def test_publish_date_northern_ireland_assembly():
    publish_date = NorthernIrelandAssemblyElection(date(2017, 3, 2)).sopn_publish_date

    assert publish_date == date(2017, 2, 8)
