from organisations.models import Organisation

class IDMaker(object):
    def __init__(self, election_type, date,
                 organisation=None, subtype=None, division=None):
        self.election_type = election_type
        self.date = date
        self.use_org = True
        if organisation.organisation_type == election_type.election_type:
            self.organisation = Organisation.objects.get(
                organisation_type=election_type.election_type)
            self.use_org = False
        else:
            self.organisation = organisation
        self.subtype = subtype
        self.division = division

    def _get_parts(self):
        parts = []
        parts.append(self.election_type.election_type)
        if self.subtype:
            parts.append(self.subtype.election_subtype)
        if self.use_org and self.organisation:
            if isinstance(self.organisation, Organisation):
                parts.append(self.organisation.slug)
            else:
                parts.append(self.organisation)
        if self.division:
            parts.append(self.division.slug)
        parts.append(self._format_date(self.date))
        return parts

    def _format_date(self, date):
        return self.date.strftime("%Y-%m-%d")

    def to_title(self):
        parts = []
        if self.organisation:
            parts.append(self.organisation.election_name)
        if self.subtype:
            parts.append("({})".format(self.subtype.name))
        return " ".join(parts).strip()


    def to_id(self):
        return ".".join(self._get_parts())
