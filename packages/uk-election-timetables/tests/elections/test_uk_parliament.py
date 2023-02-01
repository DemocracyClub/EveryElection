import pytest
from datetime import date

from uk_election_timetables.calendars import Country
from uk_election_timetables.elections import UKParliamentElection


# Reference election: parl.aberavon.2017-06-08
def test_publish_date_uk_parliament_wales():
    election = UKParliamentElection(date(2017, 6, 8), Country.WALES)

    assert election.sopn_publish_date == date(2017, 5, 11)


# Reference election: parl.na-h-eileanan-an-iar.2017-06-08
def test_publish_date_uk_parliament_scotland():
    election = UKParliamentElection(date(2017, 6, 8), Country.SCOTLAND)

    assert election.sopn_publish_date == date(2017, 5, 11)


# Reference election: parl.belfast-east.2017-06-08
def test_publish_date_uk_parliament_northern_ireland():
    election = UKParliamentElection(date(2017, 6, 8), Country.NORTHERN_IRELAND)

    assert election.sopn_publish_date == date(2017, 5, 11)


# Reference election: parl.hemel-hempstead.2017-06-08
def test_publish_date_uk_parliament_england():
    election = UKParliamentElection(date(2017, 6, 8), Country.ENGLAND)

    assert election.sopn_publish_date == date(2017, 5, 11)


# Reference election: parl.2019-12-12
def test_publish_date_uk_parliament_2019():
    election = UKParliamentElection(date(2019, 12, 12))

    assert election.sopn_publish_date == date(2019, 11, 14)


# Reference election: parl.2019-12-12
def test_postal_vote_application_deadline_uk_parliament_2019():
    election = UKParliamentElection(date(2019, 12, 12))

    assert election.postal_vote_application_deadline == date(2019, 11, 26)


@pytest.mark.parametrize(
    "country, deadline_date",
    [
        (Country.ENGLAND, date(2023, 4, 3)),
        (Country.SCOTLAND, date(2023, 4, 4)),  # No Easter Monday BH in Scotland
        (Country.WALES, date(2023, 4, 3)),
    ],
)
def test_vac_application_deadline_uk_parliament(country, deadline_date):
    election = UKParliamentElection(date(2023, 4, 13), country=country)
    assert election.vac_application_deadline == deadline_date
