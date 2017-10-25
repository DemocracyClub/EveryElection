from datetime import datetime

from django.db import transaction

from organisations.models import Organisation, OrganisationDivision
from elections.models import Election, ElectedRole, ElectionType, VotingSystem
from uk_election_ids.election_ids import IdBuilder


class IDMaker(object):
    def __init__(self, election_type, date, organisation=None, subtype=None,
                 division=None, is_group_id=False, group_id=None,
                 group_type=None, contest_type=None, source='',
                 snooped_election_id=None):

        if type(election_type) == str:
            election_type = ElectionType.objects.get(
                election_type=election_type)
        self.election_type = election_type

        if type(date) == str:
            date = datetime.strptime(date, "%Y-%m-%d")
        self.date = date

        if self.date is None:
            self.date_known = False
        else:
            self.date_known = True
        self.is_group_id = is_group_id
        self.group_id = group_id

        override_group_types = [
            'mayor',
        ]
        if self.election_type.election_type in override_group_types:
            if self.is_group_id:
                self.group_type = "election"
            else:
                self.group_type = "organisation"
        else:
            self.group_type = group_type
        self.use_org = True
        if organisation:
            if organisation.organisation_type == election_type.election_type:
                self.organisation = Organisation.objects.get(
                    organisation_type=election_type.election_type)
                self.use_org = False
            else:
                self.organisation = organisation
        else:
            self.use_org = False
            self.organisation = None
        self.subtype = subtype
        self.division = division

        try:
            self.elected_role = ElectedRole.objects.get(
                organisation=self.organisation,
                election_type=self.election_type)
        except:
            self.elected_role = None

        self.voting_system = self.get_voting_system()
        self.contest_type = contest_type
        self.notice = None
        self.source = source
        self.snooped_election_id = snooped_election_id

    def __repr__(self):
        return self.to_id()

    def to_title(self):
        parts = []
        if self.use_org and self.organisation:
            parts.append(self.organisation.election_name)
        if self.division:
            parts.append("{}".format(self.division.name))
        if self.subtype:
            parts.append("({})".format(self.subtype.name))
        if self.contest_type == "by_election":
            parts.append('by-election')
        return " ".join(parts).strip()

    def to_id(self, tmp_id=None):
        if self.date_known:
            id = IdBuilder(self.election_type.election_type, self.date)
        else:
            id = IdBuilder(self.election_type.election_type, IdBuilder.TEMP)
        if self.subtype:
            id = id.with_subtype(self.subtype.election_subtype)
        if self.use_org and self.organisation:
            id = id.with_organisation(self.organisation.slug)
        if self.division:
            id = id.with_division(self.division.slug)
        if self.contest_type == "by_election":
            id = id.with_contest_type('by')

        if not self.is_group_id:
            return id.ballot_id
        else:
            if self.group_type == "election":
                return id.election_group_id
            else:
                return id.organisation_group_id

    def __eq__(self, other):
        return other.to_id() == self.to_id()

    def get_voting_system(self):
        if self.use_org:
            if self.organisation.territory_code == "SCT" and \
                    self.election_type.election_type == "local":
                return VotingSystem.objects.get(slug="STV")
        return self.election_type.default_voting_system

    @transaction.atomic
    def save_model(self):
        """
        Performs a `get_or_create` on a model with this ID
        """

        group_model = None
        if self.group_id:
            group_model = getattr(self.group_id, 'model', None)
            if not group_model:
                group_model = self.group_id.save_model()

        default_kwargs = {
            'election_type':  self.election_type,
            'election_title': self.to_title(),
            'election_subtype':  self.subtype,
            'organisation':  self.organisation,
            'division':  self.division,
            'group':  group_model,
            'group_type':  self.group_type,
            'elected_role':  self.elected_role,
            'voting_system': self.voting_system,
            'notice': self.notice,
            'source': self.source,
            'snooped_election_id': self.snooped_election_id,
        }

        try:
            existing_model = Election.objects.get(
                election_id=None,
                **default_kwargs
            )
            self.model = existing_model
        except Election.DoesNotExist:
            existing_model = None

        if existing_model and self.date_known:
            existing_model.poll_open_date = self.date
            existing_model.election_id = self.to_id()
            existing_model.save()
            return existing_model
        elif self.date_known and not existing_model:
            default_kwargs['poll_open_date'] = self.date
            new_model, _ = Election.objects.update_or_create(
                election_id=self.to_id(), defaults=default_kwargs)
            return new_model
        else:
            # We will only allow one tmp ID per (type, subtype, org)
            # Assuming that we will never know of two upcoming elections
            # that wont have the same date
            new_model, _ = Election.objects.update_or_create(**default_kwargs)
            tmp_election_id = self.to_id(tmp_id=new_model.pk)
            new_model.tmp_election_id = tmp_election_id
            new_model.save()
            self.model = new_model
            return new_model


def create_ids_for_each_ballot_paper(all_data, subtypes=None):
    all_ids = []
    for organisation in all_data.get('election_organisation', []):
        group_id = None
        if type(organisation) == str:
            organisation = Organisation.objects.get(
                organisation_type=organisation)
        pk = str(organisation.pk)
        div_data = {
            k: v for k, v
            in all_data.items()
            if str(k).startswith(pk)
            and '__' in str(k)
            and v != "no_seats"
            and v != ""
        }

        args = [all_data['election_type'], all_data['date']]
        kwargs = {
            'organisation': organisation,
        }

        election_type = all_data['election_type'].election_type
        organisation_type = organisation.organisation_type

        # GROUP 1
        # Make a group ID for the date and election type
        date_id = IDMaker(*args, is_group_id=True, group_type="election")
        if date_id not in all_ids:
            all_ids.append(date_id)

        # GROUP 2
        # Make a group ID for the date, election type and org
        if div_data:
            if election_type != organisation_type:
                group_id = IDMaker(
                    is_group_id=True,
                    group_type="organisation",
                    group_id=date_id,
                    *args, **kwargs)
                if group_id not in all_ids:
                    all_ids.append(group_id)
            else:
                group_id = date_id

        if all_data['election_type'].election_type == "mayor":
            group_id = date_id
            mayor_id = IDMaker(
                group_id=group_id,
                is_group_id=False,
                source=all_data.get('source', ''),
                snooped_election_id=all_data.get('radar_id', None),
                *args, **kwargs)
            if mayor_id not in all_ids:
                all_ids.append(mayor_id)

        if subtypes:
            for subtype in all_data.get('election_subtype', []):
                for div in div_data:
                    org_div = OrganisationDivision.objects.get(
                        pk=div.split('__')[1]
                    )

                    all_ids.append(IDMaker(
                        *args,
                        subtype=subtype,
                        division=org_div,
                        group_id=group_id,
                        source=all_data.get('source', ''),
                        snooped_election_id=all_data.get('radar_id', None),
                        **kwargs))
        else:
            for div, contest_type in div_data.items():
                org_div = OrganisationDivision.objects.get(
                    pk=div.split('__')[1]
                )
                all_ids.append(IDMaker(
                    *args,
                    division=org_div,
                    group_id=group_id,
                    contest_type=contest_type,
                    source=all_data.get('source', ''),
                    snooped_election_id=all_data.get('radar_id', None),
                    **kwargs
                    ))
    return all_ids


def get_notice_directory(elections):
    """
    given a list of IDMaker objects work out a
    sensible place to store the notice of election doc
    """

    election_group_id = ''
    organisation_group_id = ''
    ballot_id = ''
    ballot_count = 0
    for election in elections:
        if election.is_group_id and election.group_type == 'election':
            election_group_id = election.to_id()
        if election.is_group_id and election.group_type == 'organisation':
            organisation_group_id = election.to_id()
        if not election.is_group_id:
            if ballot_count == 0:
                ballot_id = election.to_id()
            else:
                ballot_id = ''
            ballot_count = ballot_count + 1

    if ballot_count == 1 and ballot_id:
        return ballot_id
    elif organisation_group_id:
        return organisation_group_id
    elif election_group_id:
        return election_group_id

    # if we get here, something went wrong
    # the function might have been called with an empty list
    raise ValueError("Can't find an appropriate election id")
