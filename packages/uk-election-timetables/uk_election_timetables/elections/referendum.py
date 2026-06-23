import datetime as dt

from uk_election_timetables.election import Election


class Referendum(Election):
    @property
    def sopn_publish_date(self) -> dt.date:
        raise NotImplementedError("No SOPN date for referenda")

    @property
    def notice_of_election_deadline(self) -> dt.date:
        raise NotImplementedError(
            "No Notice of Election Deadline for referenda"
        )
