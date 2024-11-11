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
        additions_count: int = diff_bank_holidays()
        print(f"No. of additions: {additions_count}")
        sys.exit(additions_count)
    elif args.update:
        update_bank_holidays()
        print("Update complete")
    else:
        print("No action provided. Check --help for a list of actions.")
