from datetime import datetime
from organisations.models import Organisation, OrganisationDivision, OrganisationDivisionSet
from elections.models import (
    Election, ElectedRole, ElectionSubType, ElectionType, VotingSystem)
from uk_election_ids.election_ids import IdBuilder


class ElectionBuilder:

    def __init__(self, election_type, date):

        # init params
        if type(election_type) == str:
            election_type = ElectionType.objects.get(
                election_type=election_type)
        self.election_type = election_type

        if type(date) == str:
            date = datetime.strptime(date, "%Y-%m-%d")
        if type(date) == datetime:
            date = date.date()
        self.date = date

        # Initialise an IdBuiler object.
        # We'll build up an id string progressively
        # as we add properties to the election object
        self.id = IdBuilder(self.election_type.election_type, self.date)

        # core election data
        self.subtype = None
        self.organisation = None
        self.division = None
        self.contest_type = None

        # meta-data
        self._use_org = False
        self.notice = None
        self.source = ''
        self.snooped_election_id = None

    def with_subtype(self, subtype):
        valid_subtypes = ElectionSubType.objects.filter(
            election_type=self.election_type)
        if subtype not in valid_subtypes:
            raise ElectionSubType.ValidationError(
                "'%s' is not a valid subtype for election type '%s'" %\
                (subtype, self.election_type)
            )

        self.id = self.id.with_subtype(subtype.election_subtype)
        self.subtype = subtype
        return self

    def with_organisation(self, organisation):
        valid_election_types = organisation.election_types.all()
        if self.election_type not in valid_election_types:
            raise Organisation.ValidationError(
                "'%s' is not a valid organisation for election type '%s'" %\
                (organisation, self.election_type)
            )

        # if this is a top-level group id
        # we associate the election object with an organisation
        # but the organisation doesn't form part of the id
        if organisation.organisation_type == self.election_type.election_type:
            self._use_org = False
            self.organisation = Organisation.objects.get(
                organisation_type=self.election_type.election_type)
        else:
            self._use_org = True
            self.id = self.id.with_organisation(organisation.slug)
            self.organisation = organisation
        return self

    def with_division(self, division):
        if division.organisation != self.organisation:
            raise OrganisationDivision.ValidationError(
                "'%s' is not a child of '%s'" %\
                (division, self.organisation)
            )

        divisionset = division.divisionset

        if divisionset.start_date and divisionset.start_date > self.date:
            raise OrganisationDivisionSet.ValidationError(
                'DivisionSet start date after election date')
        if divisionset.end_date and divisionset.end_date < self.date:
            raise OrganisationDivisionSet.ValidationError(
                'DivisionSet end date before election date')

        self.id = self.id.with_division(division.slug)
        self.division = division
        return self

    def with_contest_type(self, contest_type):
        self.id = self.id.with_contest_type(contest_type)
        self.contest_type = contest_type
        return self

    def with_source(self, source):
        self.source = source
        return self

    def with_snooped_election(self, id):
        self.snooped_election_id = id
        return self

    def get_elected_role(self):
        if not self.organisation:
            return None

        try:
            return ElectedRole.objects.get(
                organisation=self.organisation,
                election_type=self.election_type)
        except ElectedRole.DoesNotExist:
            return None

    def get_voting_system(self):
        # Scottish council elections use Single Transferrable Vote
        if self._use_org:
            if self.organisation.territory_code == "SCT" and \
                    self.election_type.election_type == "local":
                return VotingSystem.objects.get(slug="STV")

        # The Constituency ballots in an Additional Member System
        # election are essentially FPTP
        if self.election_type.default_voting_system.slug == 'AMS' and\
                self.subtype and self.subtype.election_subtype == 'c':
            return VotingSystem.objects.get(slug="FPTP")

        # otherwise we can rely on the election type
        return self.election_type.default_voting_system

    def __repr__(self):
        return self.id.__repr__()

    def to_title(self, id_type):
        if id_type == 'election':
            return self.election_type.name
        if id_type == 'subtype':
            return "{election} ({subtype})".format(
                election=self.election_type.name,
                subtype=self.subtype.name
            )

        parts = []
        if self._use_org and self.organisation:
            parts.append(self.organisation.election_name)
        if self.division:
            parts.append("{}".format(self.division.name))
        if self.subtype:
            parts.append("({})".format(self.subtype.name))
        if self.contest_type == "by":
            parts.append('by-election')
        return " ".join(parts).strip()

    def __eq__(self, other):
        return self.id.__eq__(other.id)

    def _build(self, record):

        def merge_dicts(d1, d2):
            d3 = d1.copy()
            d3.update(d2)
            return d3

        try:
            return Election.objects.get(election_id=record['election_id'])
        except Election.DoesNotExist:
            # return an instance of elections.models.Election
            # but don't persist it to the DB yet.
            # The calling code is responsible for calling .save()
            return Election(**merge_dicts(record, {
                'poll_open_date': self.date,
                'election_type': self.election_type,
                'election_subtype': self.subtype,
                'organisation': self.organisation,
                'division': self.division,
                'elected_role': self.get_elected_role(),
                'voting_system': self.get_voting_system(),
            }))

    def build_election_group(self):
        return self._build({
            'election_id': self.id.election_group_id,
            'election_title': self.to_title('election'),
            'group': None,
            'group_type': 'election',
            'notice': None,
            'source': '',
            'snooped_election_id': None,
        })

    def build_subtype_group(self, group):
        return self._build({
            'election_id': self.id.subtype_group_id,
            'election_title': self.to_title('subtype'),
            'group': group,
            'group_type': 'subtype',
            'notice': None,
            'source': '',
            'snooped_election_id': None,
        })

    def build_organisation_group(self, group):
        return self._build({
            'election_id': self.id.organisation_group_id,
            'election_title': self.to_title('organisation'),
            'group': group,
            'group_type': 'organisation',
            'notice': None,
            'source': '',
            'snooped_election_id': None,
        })

    def build_ballot(self, group):
        return self._build({
            'election_id': self.id.ballot_id,
            'election_title': self.to_title('ballot'),
            'group': group,
            'group_type': None,
            'notice': self.notice,
            'source': self.source,
            'snooped_election_id': self.snooped_election_id,
        })


def create_ids_for_each_ballot_paper(all_data, subtypes=None):
    all_ids = []
    for organisation in all_data.get('election_organisation', []):
        group_id = None

        pk = str(organisation.pk)
        div_data = {
            k: v for k, v
            in all_data.items()
            if str(k).startswith(pk)
            and '__' in str(k)
            and v != "no_seats"
            and v != ""
        }

        election_type = all_data['election_type'].election_type
        organisation_type = organisation.organisation_type

        # GROUP 1
        # Make a group ID for the date and election type
        builder = ElectionBuilder(all_data['election_type'], all_data['date'])
        if all_data['election_type'].election_type not in ["local", "mayor", "pcc"]:
            builder.with_organisation(organisation)
        date_id = builder.build_election_group()

        if date_id.election_id not in [e.election_id for e in all_ids]:
            all_ids.append(date_id)

        # GROUP 2
        # Make a group ID for the date, election type and org
        if div_data:
            if election_type != organisation_type:
                group_id = ElectionBuilder(
                    all_data['election_type'], all_data['date'])\
                    .with_organisation(organisation)\
                    .build_organisation_group(date_id)
                if group_id.election_id not in [e.election_id for e in all_ids]:
                    all_ids.append(group_id)
            else:
                group_id = date_id

        if all_data['election_type'].election_type in ["mayor", "pcc"]:
            group_id = date_id
            mayor_id = ElectionBuilder(
                all_data['election_type'], all_data['date'])\
                .with_organisation(organisation)\
                .with_source(all_data.get('source', ''))\
                .with_snooped_election(all_data.get('radar_id', None))\
                .build_ballot(group_id)
            if mayor_id.election_id not in [e.election_id for e in all_ids]:
                all_ids.append(mayor_id)

        if subtypes:
            for subtype in all_data.get('election_subtype', []):

                subtype_id = ElectionBuilder(
                    all_data['election_type'], all_data['date'])\
                    .with_subtype(subtype)\
                    .with_organisation(organisation)\
                    .with_source(all_data.get('source', ''))\
                    .with_snooped_election(all_data.get('radar_id', None))\
                    .build_subtype_group(group_id)
                if subtype_id.election_id not in [e.election_id for e in all_ids]:
                    all_ids.append(subtype_id)

                for div, contest_type in div_data.items():
                    org_div = OrganisationDivision.objects.get(
                        pk=div.split('__')[1]
                    )

                    builder = ElectionBuilder(
                        all_data['election_type'], all_data['date'])\
                        .with_subtype(subtype)\
                        .with_organisation(organisation)\
                        .with_division(org_div)\
                        .with_source(all_data.get('source', ''))\
                        .with_snooped_election(all_data.get('radar_id', None))

                    if contest_type == 'by_election':
                        all_ids.append(
                            builder.with_contest_type('by').build_ballot(subtype_id))
                    elif contest_type in ['contested', 'seats_contested']:
                        all_ids.append(builder.build_ballot(subtype_id))
                    else:
                        raise ValueError("Unrecognised contest_type value '%s'" % contest_type)
        else:
            for div, contest_type in div_data.items():
                org_div = OrganisationDivision.objects.get(
                    pk=div.split('__')[1]
                )

                builder = ElectionBuilder(
                    all_data['election_type'], all_data['date'])\
                    .with_organisation(organisation)\
                    .with_division(org_div)\
                    .with_source(all_data.get('source', ''))\
                    .with_snooped_election(all_data.get('radar_id', None))

                if contest_type == 'by_election':
                    all_ids.append(
                        builder.with_contest_type('by').build_ballot(group_id))
                elif contest_type in ['contested', 'seats_contested']:
                    all_ids.append(builder.build_ballot(group_id))
                else:
                    raise ValueError("Unrecognised contest_type value '%s'" % contest_type)
    return all_ids


def get_notice_directory(elections):
    """
    given a list of Election objects work out a
    sensible place to store the notice of election doc
    """

    election_group_id = ''
    organisation_group_id = ''
    ballot_id = ''
    ballot_count = 0
    for election in elections:
        if election.group_type == 'election':
            election_group_id = election.election_id
        elif election.group_type == 'organisation':
            organisation_group_id = election.election_id
        elif not election.group_type:
            if ballot_count == 0:
                ballot_id = election.election_id
            else:
                ballot_id = ''
            ballot_count = ballot_count + 1
        else:
            raise ValueError("unrecognised Election group_type '%s'" % (election.group_type))

    if ballot_count == 1 and ballot_id:
        return ballot_id
    elif organisation_group_id:
        return organisation_group_id
    elif election_group_id:
        return election_group_id

    # if we get here, something went wrong
    # the function might have been called with an empty list
    raise ValueError("Can't find an appropriate election id")
