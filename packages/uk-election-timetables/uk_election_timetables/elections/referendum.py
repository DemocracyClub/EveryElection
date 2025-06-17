from datetime import date

from uk_election_timetables.election import Election


class Referendum(Election):
    @property
    def sopn_publish_date(self) -> date:
        raise NotImplementedError("No SOPN date for referenda")
