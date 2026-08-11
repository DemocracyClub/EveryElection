# uk-election-timetables

## Setup

This is a UV [package workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) inside Every Election.

If you only want to work on the uk-election-timetables library, you can run

```
uv sync --package uk-election-timetables
```

to install only the package dependencies.

## Test

```
pytest
```

## Updating Bank Holiday Dates

This project checks daily for additions to the government bank holiday dataset at https://www.gov.uk/bank-holidays.json. When an addition is identified in the .gov file, this project will automatically create a GitHub issue to update our local bank holiday dataset.

To update `bank-holidays.json` with additions from the government supplied file, run the following within your venv:
```commandline
python manage_bank_holidays.py --update
```

This is set to run automatically on a schedule
https://github.com/DemocracyClub/EveryElection/actions/workflows/check-for-bank-holiday-updates.yml

## Documentation

```
uv sync --package uk-election-timetables --group docs
```

There are sphinx docs, and it is possible to build them but they need a bit of work.

## Package release

Create and tag a GitHub release. A GitHub workflow will automatically build and push the package to PyPI on release.
