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
        try:
            current_events: List = existing_dataset[key]["events"]
            new_events: List = new_dataset[key]["events"]
        except KeyError as ex:
            print(f"Unable to find key: {ex}")
            return 0
        total_count += sum([1 for x in new_events if x not in current_events])
    return total_count
