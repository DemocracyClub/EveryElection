import datetime as dt

import pytest

from uk_election_timetables.calendars import Country
from uk_election_timetables.elections import UKParliamentElection


# Reference election: parl.aberavon.2017-06-08
def test_publish_date_uk_parliament_wales():
    election = UKParliamentElection(dt.date(2017, 6, 8), Country.WALES)

    assert election.sopn_publish_date == dt.date(2017, 5, 11)


# Reference election: parl.na-h-eileanan-an-iar.2017-06-08
def test_publish_date_uk_parliament_scotland():
    election = UKParliamentElection(dt.date(2017, 6, 8), Country.SCOTLAND)

    assert election.sopn_publish_date == dt.date(2017, 5, 11)


# Reference election: parl.belfast-east.2017-06-08
def test_publish_date_uk_parliament_northern_ireland():
    election = UKParliamentElection(
        dt.date(2017, 6, 8), Country.NORTHERN_IRELAND
    )

    assert election.sopn_publish_date == dt.date(2017, 5, 11)


# Reference election: parl.hemel-hempstead.2017-06-08
def test_publish_date_uk_parliament_england():
    election = UKParliamentElection(dt.date(2017, 6, 8), Country.ENGLAND)

    assert election.sopn_publish_date == dt.date(2017, 5, 11)


# Reference election: parl.2019-12-12
def test_publish_date_uk_parliament_2019():
    election = UKParliamentElection(dt.date(2019, 12, 12))

    assert election.sopn_publish_date == dt.date(2019, 11, 14)


# Reference election: parl.2019-12-12
def test_postal_vote_application_deadline_uk_parliament_2019():
    election = UKParliamentElection(dt.date(2019, 12, 12))

    assert election.postal_vote_application_deadline == dt.date(2019, 11, 26)


# Reference election: parl.2024-07-04
def test_notice_of_election_deadline():
    election = UKParliamentElection(dt.date(2024, 7, 4))

    assert election.notice_of_election_deadline == dt.date(2024, 6, 4)


@pytest.mark.parametrize(
    "country, deadline_date",
    [
        (Country.ENGLAND, dt.date(2023, 4, 3)),
        # No Easter Monday BH in Scotland
        # and Easter Monday is non special-cased for Scotland in
        # The Voter Identification Regulations 2022
        (Country.SCOTLAND, dt.date(2023, 4, 4)),
        (Country.WALES, dt.date(2023, 4, 3)),
    ],
)
def test_vac_application_deadline_uk_parliament(country, deadline_date):
    election = UKParliamentElection(dt.date(2023, 4, 13), country=country)
    assert election.vac_application_deadline == deadline_date
