from typing import Dict, List


def get_additions_count(existing_dataset: Dict, new_dataset: Dict) -> int:
    """
    Get the number of additions in new_dataset when compared to existing_dataset
    :param existing_dataset: Seeded dict of historical dates (usually bank-holidays.json)
    :param new_dataset: Dict of new bank holiday dates (usually https://www.gov.uk/bank-holidays.json)
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
    :param existing_dataset: Seeded dict of historical dates (usually bank-holidays.json)
    :param new_dataset: Dict of new bank holiday dates (usually https://www.gov.uk/bank-holidays.json)
    :return: Dict
    """
    combined_dataset = existing_dataset
    for key in new_dataset.keys():
        current_events: List = existing_dataset.get(key, {}).get("events", [])
        new_events: List = new_dataset.get(key, {}).get("events", [])
        all_events = current_events + [x for x in new_events if x not in current_events]

        all_events = sorted(all_events, key=lambda d: d['date'])
        combined_dataset[key]["events"] = all_events

    return combined_dataset

