from organisations.models import Organisation

class IDMaker(object):
    def __init__(self, election_type, date, organisation=None, subtype=None):
        self.election_type = election_type
        self.date = date
        if organisation == election_type.election_type:
            self.organisation = None
        else:
            self.organisation = organisation
        self.subtype = subtype

    def _get_parts(self):
        parts = []
        parts.append(self.election_type.election_type)
        if self.subtype:
            parts.append(self.subtype.election_subtype)
        if self.organisation:
            if isinstance(self.organisation, Organisation):
                parts.append(self.organisation.slug)
            else:
                parts.append(self.organisation)
        parts.append(self._format_date(self.date))
        return parts

    def _format_date(self, date):
        return self.date.strftime("%Y-%m-%d")

    def to_id(self):
        return ".".join(self._get_parts())
