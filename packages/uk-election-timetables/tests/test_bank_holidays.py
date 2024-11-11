import copy
from typing import Dict

import pytest

from uk_election_timetables.bank_holidays import (
    combine_bank_holiday_lists,
    get_additions_count,
)

from .data.bank_holidays import (
    base_data,
    changed_name,
    changed_name_and_date,
    complete_data,
)
from .data.bank_holidays import (
    single_historical_event_per_division as historical_data,
)
from .data.bank_holidays import (
    single_new_event_per_division as gov_data,
)


@pytest.mark.parametrize(
    "existing_dataset, new_dataset, expected_count",
    [
        (base_data, gov_data, 3),  # New events from .gov recognised as changes
        (
            historical_data,
            base_data,
            0,
        ),  # Historical events in our dataset aren't recognised as changes
        (
            base_data,
            base_data,
            0,
        ),  # Identical datasets not recognised as changes
        ({}, {}, 0),  # Improperly formatted datasets
    ],
)
def test_get_additions_count(
    existing_dataset: Dict, new_dataset: Dict, expected_count: int
):
    diff: int = get_additions_count(existing_dataset, new_dataset)
    assert diff == expected_count


@pytest.mark.parametrize(
    "existing_dataset, new_dataset, expected_result",
    [
        (
            historical_data,
            gov_data,
            complete_data,
        ),  # All the old and new data combined
        (historical_data, historical_data, historical_data),  # No changes
        (base_data, changed_name, changed_name),  # Change to event name only
        (
            base_data,
            changed_name_and_date,
            changed_name_and_date,
        ),  # Change to event date and name
    ],
)
def test_combine_bank_holiday_lists(
    existing_dataset: Dict, new_dataset: Dict, expected_result: Dict
):
    existing_dataset_copy: Dict = copy.deepcopy(existing_dataset)
    new_dataset_copy: Dict = copy.deepcopy(new_dataset)
    new_dict: Dict = combine_bank_holiday_lists(
        existing_dataset_copy, new_dataset_copy
    )
    assert new_dict == expected_result
