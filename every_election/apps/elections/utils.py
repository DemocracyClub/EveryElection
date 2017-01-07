from django.db import transaction

from organisations.models import Organisation, OrganisationDivision
from elections.models import Election


class IDMaker(object):
    def __init__(self, election_type, date,
                 organisation=None, subtype=None,
                 division=None, is_group_id=False, group_id=None):
        self.election_type = election_type
        self.date = date
        if self.date is None:
            self.date_known = False
        else:
            self.date_known = True
        self.is_group_id = is_group_id
        self.group_id = group_id
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

    def _get_parts(self, tmp_id=None):
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
        return " ".join(parts).strip()

    def to_id(self, tmp_id=None):
        return ".".join(self._get_parts(tmp_id))

    def __eq__(self, other):
        return other.to_id() == self.to_id()

    @transaction.atomic
    def save_model(self):
        """
        Performs a `get_or_create` on a model with this ID
        """

        group_model = None
        if self.group_id and not self.is_group_id:
            group_model = getattr(self.group_id, 'model', None)
            if not group_model:
                group_model = self.group_id.save_model()

        default_kwargs = {
            'poll_open_date':  self.date,
            'election_type':  self.election_type,
            'election_subtype':  self.subtype,
            'organisation':  self.organisation,
            'division':  self.division,
            'group':  group_model,
        }

        if self.date_known:
            new_model, _ = Election.objects.update_or_create(
                election_id=self.to_id(), **default_kwargs)
            return new_model
        else:
            # We will only allow one tmp ID per (type, subtype, org)
            # Assuming that we will never know of two upcoming elections
            # that wont have the same date
            try:
                existing_model = Election.objects.get(
                    election_id=None,
                    **default_kwargs
                )
                self.model = existing_model
                return existing_model
            except Election.DoesNotExist:
                existing_model = None

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

        # GROUP 1
        # Make a group ID for the date and election type
        date_id = IDMaker(*args, is_group_id=True)
        if date_id not in all_ids:
            all_ids.append(date_id)

        # GROUP 2
        # Make a group ID for the date, election type and org
        if div_data:
            group_id = IDMaker(is_group_id=True, *args, **kwargs)
            if group_id not in all_ids:
                all_ids.append(group_id)

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
                        **kwargs))
        else:
            for div in div_data:
                org_div = OrganisationDivision.objects.get(
                    pk=div.split('__')[1]
                )
                all_ids.append(IDMaker(
                    *args,
                    division=org_div,
                    group_id=group_id,
                    **kwargs
                    ))
    return all_ids


# def create_ids_grouped(all_data, subtypes=None):
#     all_ids = []
#     for organisation in all_data.get('election_organisation', []):
#         if type(organisation) == str:
#             organisation = Organisation.objects.get(
#                 organisation_type=organisation)
#         pk = str(organisation.pk)
#
#         div_data = {
#             k: v for k, v
#             in all_data.items()
#             if str(k).startswith(pk)
#             and '__' in str(k)
#             and v != "no_seats"
#         }
#
#         by_elections = {
#             k: v for k, v
#             in div_data.items()
#             if v == "by_election"
#         }
#
#         only_by_election = by_elections == div_data
#
#         args = [all_data['election_type'], all_data['date']]
#         kwargs = {
#             'organisation': organisation,
#         }
#
#         if subtypes:
#             for subtype in all_data.get('election_subtype', []):
#                 by_elections = {
#                     k: v for k, v
#                     in div_data.items()
#                     if v == "by_election"
#                     and k.endswith(subtype.election_subtype)
#                 }
#                 only_by_election = by_elections == div_data
#                 if only_by_election:
#                     for div in by_elections:
#                         org_div = OrganisationDivision.objects.get(
#                             pk=div.split('__')[1]
#                         )
#
#                         all_ids.append(IDMaker(
#                             *args,
#                             subtype=subtype,
#                             division=org_div,
#                             **kwargs))
#                 else:
#                     all_ids.append(
#                         IDMaker(*args, subtype=subtype, **kwargs))
#         else:
#             if only_by_election:
#                 for div in by_elections:
#                     org_div = OrganisationDivision.objects.get(
#                         pk=div.split('__')[1]
#                     )
#                     all_ids.append(IDMaker(
#                         *args,
#                         division=org_div,
#                         **kwargs
#                         ))
#             else:
#                 all_ids.append(IDMaker(*args, **kwargs))
#
#     return all_ids
