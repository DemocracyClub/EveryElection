# Overview

*Given the polling day of an election in the UK, when should the Statement of Persons Nominated (SoPN) be published?*

When an election is called in the United Kingdom, the voting public must have access to the list of candidates who have been nominated to that post.

These documents are called Statements of Persons Nominated, and must be published a set number of working days ahead of the actual election date. The number varies based on:

 * *Type of Post* - Parliamentary, Local, devolved Government, etc.
 * *Country* - The United Kingdom has up to four different rules for the same type of election, one for each country.
 * *Calendar* - each country has their own unique set of Bank Holidays.


This library encapsulates timetable legislation for elections run in the United Kingdom and its devolved administrations.

## Usage

```python

from uk_election_timetables.sopnimport StatementPublishDate
from datetime import date

publish_date = StatementPublishDate()

print(publish_date.national_assembly_for_wales(date(2016, 5, 5)))

# datetime.date(2016, 4, 7)
```
 
## Installation

`pip install sopn_publish_date`
 
## Third-Party Sources
 
 The bank holidays JSON used in this project is provided by [gov.uk](https://www.gov.uk/bank-holidays.json) under the [Open Government Licence](http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
