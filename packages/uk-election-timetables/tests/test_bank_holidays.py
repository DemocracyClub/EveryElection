import pytest
from typing import Dict
from .data.bank_holidays import (
    existing_data as seed_data,
    single_new_event_per_division as gov_data,
    single_historical_event_per_division as historical_data
)
from uk_election_timetables.bank_holidays import get_additions_count

@pytest.mark.parametrize(
    "existing_dataset, new_dataset, expected_count",
    [
        (seed_data, gov_data, 3),  # New events from .gov recognised as changes
        (historical_data, seed_data, 0),  # Historical events aren't recognised as changes
        (seed_data, seed_data, 0),  # Identical datasets not recognised as changes
        ({}, {}, 0)  # Improperly formatted datasets
    ]
)
def test_get_additions_count(existing_dataset: Dict, new_dataset: Dict, expected_count: int):
    diff = get_additions_count(existing_dataset, new_dataset)
    assert diff == expected_count
