# uk-election-timetables

[![PyPI](https://img.shields.io/pypi/v/uk-election-timetables.svg)](https://pypi.org/project/uk-election-timetables/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Installation

`pip install uk_election_timetables`

This library encapsulates timetable legislation for elections run in the United Kingdom and its devolved administrations.

The election timetable varies based on:

 * *Type of Post* - Parliamentary, Local, devolved Government, etc.
 * *Country* - The United Kingdom has up to four different rules for the same type of election, one for each country.
 * *Calendar* - each country has their own unique set of Bank Holidays.

## Usage (publishing of candidate lists)

```python
from datetime import date
from uk_election_timetables.elections.uk_parliament import UKParliamentElection

election = UKParliamentElection(date(2019, 2, 21))

print(election.close_of_nominations) # date(2019, 1, 25)
```

## Supported Election Types

 - [x] Local
 - [x] City of London Local
 - [x] United Kingdom Parliament
 - [x] Scottish Parliament
 - [x] Senedd Cymru
 - [x] Northern Ireland Assembly
 - [x] Mayoral
 - [x] Mayoral (London)
 - [x] Greater London Assembly
 - [x] Police and Crime commissioner
 - [x] Referendum
