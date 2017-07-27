from datetime import datetime

from django.db import transaction

from organisations.models import Organisation, OrganisationDivision
from elections.models import Election, ElectedRole, ElectionType, VotingSystem


class IDMaker(object):
    def __init__(self, election_type, date, organisation=None, subtype=None,
                 division=None, is_group_id=False, group_id=None,
                 group_type=None, contest_type=None, source=''):

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
        self.source = source

    def __repr__(self):
        return self.to_id()

    def _get_parts(self, tmp_id=None):
        parts = []
        parts.append(self.election_type.election_type)
        if self.subtype:
            parts.append(self.subtype.election_subtype)
        if self.use_org and self.organisation:
            parts.append(self.organisation.slug)
        if self.division:
            parts.append(self.division.slug)
        if self.contest_type == "by_election":
            parts.append('by')
        if tmp_id:
            parts.append("tmp-{}".format(tmp_id))
        else:
            parts.append(self._format_date(self.date))
        return parts

    def _format_date(self, date):
        if self.date_known:
            return self.date.strftime("%Y-%m-%d")
        else:
            return "<tmp-id>"

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
        return ".".join(self._get_parts(tmp_id))

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
            'source': self.source,
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
            'source': all_data.get('source', ''),
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
                *args, **kwargs)
            if mayor_id not in all_ids:
                all_ids.append(mayor_id)

        if subtypes:
            for subtype in all_data.get('election_subtype', []):

                subtype_id = IDMaker(
                    group_id=date_id,
                    is_group_id=True,
                    subtype=subtype,
                    *args, **kwargs)
                all_ids.append(subtype_id)

                for div in div_data:
                    org_div = OrganisationDivision.objects.get(
                        pk=div.split('__')[1]
                    )

                    all_ids.append(IDMaker(
                        *args,
                        subtype=subtype,
                        division=org_div,
                        group_id=group_id,
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
                    **kwargs
                    ))
    return all_ids
