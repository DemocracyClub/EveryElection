import sys
import argparse
from uk_election_timetables.bank_holidays import (
    diff_bank_holidays,
    update_bank_holidays,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--diff",
        action="store_true",
        help="Get number of additions in new .gov dataset",
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Update bank-holidays.json with .gov additions",
    )
    args = parser.parse_args()

    if args.diff:
        try:
            additions_count: int = diff_bank_holidays()
            print(f"No. of additions: {additions_count}")
            sys.exit(additions_count)
        except Exception as ex:
            print(f"Unable to diff files")
            sys.exit(0)
    elif args.update:
        try:
            update_bank_holidays()
            print("Update complete")
        except Exception as ex:
            print(f"Unable to update bank-holidays.json: {ex}")
    else:
        print("No action provided. Check --help for a list of actions.")
