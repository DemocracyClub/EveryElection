from datetime import datetime
from .datapackage import ELECTION_TYPES
from .parser import DataPackageParser
from .slugger import slugify


parser = DataPackageParser(ELECTION_TYPES)
RULES = parser.build_rules()
CONTEST_TYPES = ('by', 'by election', 'by-election', 'election')


class IdBuilder:

    def __init__(self, election_type, date):
        if election_type == 'ref':
            raise NotImplementedError()
        if election_type == 'eu':
            raise NotImplementedError()
        self._validate_election_type(election_type)
        self.election_type = election_type
        self.spec = RULES[self.election_type]
        self.date = self._format_date(date)
        self.subtype = None
        self.organisation = None
        self.division = None
        self.contest_type = None

    def _format_date(self, date):
        if isinstance(date, str):
            # if we've been given a string, validate it
            # by converting to a datetime and back again
            return datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")

        return date.strftime("%Y-%m-%d")

    @property
    def _can_have_divs(self):
        if isinstance(self.spec.can_have_divs, (bool,)):
            return self.spec.can_have_divs
        else:
            return self.spec.can_have_divs[self.subtype]

    def with_subtype(self, subtype):
        self._validate_subtype(subtype)
        self.subtype = subtype
        return self

    def with_organisation(self, organisation):
        if organisation is None:
            organisation = ''
        organisation = slugify(organisation)
        self._validate_organisation(organisation)
        self.organisation = organisation
        return self

    def with_division(self, division):
        if division is None:
            division = ''
        division = slugify(division)
        self._validate_division(division)
        self.division = division
        return self

    def with_contest_type(self, contest_type):
        self._validate_contest_type(contest_type)
        if contest_type.lower() in ('by', 'by election', 'by-election'):
            self.contest_type = 'by'
        return self

    def _validate_election_type(self, election_type):
        if election_type not in ELECTION_TYPES:
            raise ValueError("Allowed values for election_type are %s" %\
                (str(list(ELECTION_TYPES.keys()))))
        return True

    def _validate_subtype(self, subtype):
        if isinstance(self.spec.subtypes, tuple) and subtype not in self.spec.subtypes:
            raise ValueError("Allowed values for subtype are %s" % (str(self.spec.subtypes)))
        if not self.spec.subtypes and subtype:
            raise ValueError("election_type %s may not have a subtype" % (self.election_type))
        return True

    def _validate_organisation(self, organisation):
        if not self.spec.can_have_orgs and organisation:
            raise ValueError("election_type %s may not have an organisation" % (self.election_type))
        return True

    def _validate_division(self, division):
        try:
            can_have_divs = self._can_have_divs
        except KeyError:
            raise ValueError("election_type %s must have a valid subtype before setting a division" % (
                self.election_type))
        if not can_have_divs and division:
            raise ValueError("election_type %s may not have a division" % (self.election_type))
        return True

    def _validate_contest_type(self, contest_type):
        if not contest_type:
            return True
        if not contest_type.lower() in CONTEST_TYPES:
            raise ValueError("Allowed values for contest_type are %s" % (str(list(CONTEST_TYPES))))
        return True

    def _validate(self):
        # validation checks necessary to create any id
        self._validate_election_type(self.election_type)
        self._validate_organisation(self.organisation)
        if self.spec.can_have_orgs and self._can_have_divs and not self.organisation and self.division:
            raise ValueError("election_type %s must have an organisation in order to have a division" % (self.election_type))
        self._validate_contest_type(self.contest_type)
        return True

    @property
    def election_group_id(self):
        self._validate()
        # there are no additional validation checks for the top-level group id
        parts = []
        parts.append(self.election_type)
        parts.append(self.date)
        return ".".join(parts)

    def _validate_for_subtype_group_id(self):
        if not isinstance(self.spec.subtypes, tuple):
            raise ValueError("Can't create subtype id for election_type %s" % (self.election_type))
        if isinstance(self.spec.subtypes, tuple) and not self.subtype:
            raise ValueError("Subtype must be specified for election_type %s" % (self.election_type))
        self._validate_subtype(self.subtype)
        return True

    @property
    def subtype_group_id(self):
        self._validate()
        self._validate_for_subtype_group_id()

        parts = []
        parts.append(self.election_type)
        parts.append(self.subtype)
        parts.append(self.date)
        return ".".join(parts)

    def _validate_for_organisation_group_id(self):
        # validation checks specifically relevant to creating an organisation group id
        if isinstance(self.spec.subtypes, tuple) and not self.subtype:
            raise ValueError("Subtype must be specified for election_type %s" % (self.election_type))
        self._validate_subtype(self.subtype)
        if not self.spec.can_have_orgs:
            raise ValueError("election_type %s can not have an organisation group id" % (self.election_type))
        if self.spec.can_have_orgs and not self.organisation:
            raise ValueError("election_type %s must have an organisation in order to create an organisation group id" % (self.election_type))
        return True

    @property
    def organisation_group_id(self):
        self._validate()
        self._validate_for_organisation_group_id()

        parts = []
        parts.append(self.election_type)
        if self.subtype:
            parts.append(self.subtype)
        parts.append(self.organisation)
        parts.append(self.date)
        return ".".join(parts)

    def _validate_for_ballot_id(self):
        # validation checks specifically relevant to creating a ballot id
        if isinstance(self.spec.subtypes, tuple) and not self.subtype:
            raise ValueError("Subtype must be specified for election_type %s" % (self.election_type))
        self._validate_subtype(self.subtype)
        if self.spec.can_have_orgs and not self.organisation:
            raise ValueError("election_type %s must have an organisation in order to create a ballot id" % (self.election_type))
        if self._can_have_divs and not self.division:
            raise ValueError("election_type %s must have a division in order to create a ballot id" % (self.election_type))
        return True

    @property
    def ballot_id(self):
        self._validate()
        self._validate_division(self.division)
        self._validate_for_ballot_id()

        parts = []
        parts.append(self.election_type)
        if self.subtype:
            parts.append(self.subtype)
        if self.organisation:
            parts.append(self.organisation)
        if self.division:
            parts.append(self.division)
        if self.contest_type:
            parts.append(self.contest_type)
        parts.append(self.date)
        return ".".join(parts)

    @property
    def ids(self):
        ids = []

        try:
            ids.append(self.election_group_id)
        except ValueError:
            pass

        if isinstance(self.spec.subtypes, tuple):
            try:
                ids.append(self.subtype_group_id)
            except ValueError:
                pass

        if self.spec.can_have_orgs:
            try:
                ids.append(self.organisation_group_id)
            except ValueError:
                pass

        try:
            if self.ballot_id not in ids:
                ids.append(self.ballot_id)
        except ValueError:
            pass

        return ids

    def __repr__(self):
        return str(self.ids)

    def __eq__(self, other):
        return type(other) == IdBuilder and self.__dict__ == other.__dict__
