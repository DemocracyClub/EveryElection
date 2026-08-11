import datetime as dt

import pytest
from uk_election_timetables.elections import (
    ScottishParliamentElection,
)

sopn_test_cases = [
    {
        # Reference election: sp.c.shetland-islands.2021-05-06
        # https://candidates.democracyclub.org.uk/elections/sp.c.shetland-islands.2021-05-06/sopn/
        # In 2021 Easter Monday fell between SOPN Publish date and polling day
        "poll_date": dt.date(2021, 5, 6),
        "close_of_nominations": dt.date(2021, 3, 31),
    },
    {
        # Reference election: sp.c.shetland-islands.2016-05-05
        # https://candidates.democracyclub.org.uk/elections/sp.c.shetland-islands.2016-05-05/sopn/
        # In 2016 Easter Monday was on 27th March so does not factor in here
        "poll_date": dt.date(2016, 5, 5),
        "close_of_nominations": dt.date(2016, 4, 1),
    },
]


@pytest.mark.parametrize("election", sopn_test_cases)
def test_publish_date_scottish_parliament(election):
    assert (
        ScottishParliamentElection(election["poll_date"]).close_of_nominations
        == election["close_of_nominations"]
    )


# Reference election: sp.2021-05-06
def test_registration_deadline_scottish_parliament():
    election = ScottishParliamentElection(dt.date(2021, 5, 6))

    assert election.registration_deadline == dt.date(2021, 4, 19)


# Reference election: sp.2021-05-06
def test_postal_vote_application_deadline_scottish_parliament():
    election = ScottishParliamentElection(dt.date(2021, 5, 6))

    assert election.postal_vote_application_deadline == dt.date(2021, 4, 6)


# Reference election: sp.2026-05-07
def test_notice_of_election_deadline():
    election = ScottishParliamentElection(dt.date(2026, 5, 7))

    assert election.notice_of_election_deadline == dt.date(2026, 3, 25)
