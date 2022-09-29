import os
import json
import requests
from datetime import datetime

from typing import Dict, List

GOV_BANK_HOLIDAY_URL = "https://www.gov.uk/bank-holidays.json"
LOCAL_BANK_HOLIDAY_FILE = "bank-holidays.json"


def get_additions_count(existing_dataset: Dict, new_dataset: Dict) -> int:
    """
    Get the number of additions in new_dataset when compared to existing_dataset
    :param existing_dataset: Seeded dict of historical dates
    :param new_dataset: Dict of new bank holiday dates
    :return: int
    """
    total_count: int = 0
    for key in new_dataset.keys():
        current_events: List = existing_dataset.get(key, {}).get("events", [])
        new_events: List = new_dataset.get(key, {}).get("events", [])
        total_count += sum([1 for x in new_events if x not in current_events])

    return total_count


def combine_bank_holiday_lists(existing_dataset: Dict, new_dataset: Dict) -> Dict:
    """
    Create dict containing all values from existing dataset and all new values from new dataset
    :param existing_dataset: Seeded dict of historical dates
    :param new_dataset: Dict of new bank holiday dates
    :return: Dict
    """
    combined_dataset = existing_dataset
    for key in new_dataset.keys():
        current_events: List = existing_dataset.get(key, {}).get("events", [])
        new_events: List = new_dataset.get(key, {}).get("events", [])
        new_events = sorted(new_events, key=lambda d: d["date"])

        combined_events: List = current_events + [
            x for x in new_events if x not in current_events
        ]
        combined_events = sorted(combined_events, key=lambda d: d["date"])

        # Remove duplicated records (any events within date range of .gov list which are not present in .gov list)
        earliest_new_event: datetime.date = datetime.strptime(
            new_events[0]["date"], "%Y-%m-%d"
        ).date()
        for event in combined_events:
            event_date: datetime.date = datetime.strptime(
                event["date"], "%Y-%m-%d"
            ).date()
            if (event_date >= earliest_new_event) and (event not in new_events):
                combined_events.remove(event)

        combined_dataset[key]["events"] = combined_events

    return combined_dataset


def diff_bank_holidays() -> int:
    """
    Fetch bank holiday data from our local file and .gov source and return number of additions in diff
    :return: int
    """
    bank_holiday_json_path: str = os.path.join(
        os.path.dirname(__file__), LOCAL_BANK_HOLIDAY_FILE
    )
    with open(bank_holiday_json_path, "r") as file:
        current_data: Dict = json.load(file)

    gov_data: Dict = requests.get(GOV_BANK_HOLIDAY_URL).json()
    return get_additions_count(current_data, gov_data)


def update_bank_holidays() -> None:
    """
    Fetch bank holiday data from our local file and .gov source and perform update
    :return: None
    """
    bank_holiday_json_path: str = os.path.join(
        os.path.dirname(__file__), LOCAL_BANK_HOLIDAY_FILE
    )
    with open(bank_holiday_json_path, "r") as file:
        current_data: Dict = json.load(file)

    gov_data: Dict = requests.get(GOV_BANK_HOLIDAY_URL).json()
    updated_dataset: Dict = combine_bank_holiday_lists(current_data, gov_data)
    with open(bank_holiday_json_path, "w") as file:
        json.dump(updated_dataset, file, indent=4, ensure_ascii=False)
