from datetime import date

import pytest
from uk_election_timetables.elections import CityOfLondonLocalElection

registration_test_cases = [
    {
        "poll_date": date(2025, 1, 1),
        "expected_registration_deadline": date(2023, 11, 30),
    },
    {
        "poll_date": date(2025, 2, 15),
        "expected_registration_deadline": date(2023, 11, 30),
    },
    {
        "poll_date": date(2025, 2, 16),
        "expected_registration_deadline": date(2024, 11, 30),
    },
    {
        "poll_date": date(2025, 11, 29),
        "expected_registration_deadline": date(2024, 11, 30),
    },
]


@pytest.mark.parametrize("election", registration_test_cases)
def test_city_of_london_registration_deadline(election):
    assert (
        CityOfLondonLocalElection(election["poll_date"]).registration_deadline
        == election["expected_registration_deadline"]
    )
