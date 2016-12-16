from organisations.models import Organisation, OrganisationDivision


class IDMaker(object):
    def __init__(self, election_type, date,
                 organisation=None, subtype=None,
                 division=None, group_id=False):
        self.election_type = election_type
        self.date = date
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
        if self.use_org and self.organisation:
            parts.append(self.organisation.election_name)
        if self.subtype:
            parts.append("({})".format(self.subtype.name))
        return " ".join(parts).strip()

    def to_id(self):
        return ".".join(self._get_parts())

    def __eq__(self, other):
        return other.to_id() == self.to_id()


def create_ids_for_each_ballot_paper(all_data, subtypes=None):
    all_ids = []
    for organisation in all_data.get('election_organisation', []):
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
        date_id = IDMaker(*args, group_id=True)
        if date_id not in all_ids:
            all_ids.append(date_id)


        # GROUP 2
        # Make a group ID for the date, election type and org
        if div_data:
            org_id = IDMaker(group_id=True, *args, **kwargs)
            if org_id not in all_ids:
                all_ids.append(org_id)

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
                        **kwargs))
        else:
            for div in div_data:
                org_div = OrganisationDivision.objects.get(
                    pk=div.split('__')[1]
                )
                all_ids.append(IDMaker(
                    *args,
                    division=org_div,
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
