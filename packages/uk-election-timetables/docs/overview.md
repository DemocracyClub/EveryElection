# Overview

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

print(election.sopn_publish_date) # date(2019, 1, 25)
```
 
## Installation

`pip install uk_election_timetables`
 
## Third-Party Sources
 
 The bank holidays JSON used in this project is provided by [gov.uk](https://www.gov.uk/bank-holidays.json) under the [Open Government Licence](http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
