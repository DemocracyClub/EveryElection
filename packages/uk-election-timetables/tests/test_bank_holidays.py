import pytest
from typing import Dict
from .data.bank_holidays import (
    existing_data as seed_data,
    single_new_event_per_division as gov_data,
    single_historical_event_per_division as historical_data,
    complete_data
)
from uk_election_timetables.bank_holidays import get_additions_count, combine_bank_holiday_lists

@pytest.mark.parametrize(
    "existing_dataset, new_dataset, expected_count",
    [
        (seed_data, gov_data, 3),  # New events from .gov recognised as changes
        (historical_data, seed_data, 0),  # Historical events in our dataset aren't recognised as changes
        (seed_data, seed_data, 0),  # Identical datasets not recognised as changes
        ({}, {}, 0)  # Improperly formatted datasets
    ]
)
def test_get_additions_count(existing_dataset: Dict, new_dataset: Dict, expected_count: int):
    diff = get_additions_count(existing_dataset, new_dataset)
    assert diff == expected_count

@pytest.mark.parametrize(
    "existing_dataset, new_dataset, expected_result",
    [
        (historical_data, gov_data, complete_data),  # All the old and new data combined
        (historical_data, historical_data, historical_data)  # No changes
    ]
)
def test_combine_bank_holiday_lists(existing_dataset, new_dataset, expected_result):
    new_dict = combine_bank_holiday_lists(existing_dataset, new_dataset)
    assert new_dict == complete_data
