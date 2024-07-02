from datetime import datetime
from typing import Optional, Union

from elections.models import (
    ElectedRole,
    Election,
    ElectionSubType,
    ElectionType,
    MetaData,
)
from organisations.models import (
    Organisation,
    OrganisationDivision,
    OrganisationDivisionSet,
)
from uk_election_ids.datapackage import ELECTION_TYPES
from uk_election_ids.election_ids import IdBuilder
from uk_election_ids.metadata_tools import (
    IDRequirementsMatcher,
    VotingSystemMatcher,
)

CACHE = {
    "voting_systems": {},
    "election_types": {},
    "election_sub_types": {},
    "valid_election_types": {},
    "private_elections": {},
    "elected_roles": {},
}


def reset_cache():
    global CACHE
    NEW_CACHE = {}
    for key in CACHE:
        NEW_CACHE[key] = {}
    CACHE = NEW_CACHE


def election_type_has_divisions(election_type: Union[ElectionType, str]):
    if isinstance(election_type, ElectionType):
        election_type_str = election_type.election_type
    else:
        election_type_str = election_type

    return ELECTION_TYPES.get(election_type_str, {}).get("can_have_divs", True)


def get_voter_id_requirement(election: Election) -> Optional[str]:
    """
    Given an Election object, if eligible for voter ID return the related voter ID legislation code
    """
    can_have_divs = election_type_has_divisions(election.election_type)
    if can_have_divs and not election.division:
        return None

    nation = None
    if can_have_divs:
        nation = election.division.territory_code
        if not nation:
            return None

    matcher = IDRequirementsMatcher(election.election_id, nation)

    return matcher.get_id_requirements()


def get_cached_election_type(election_type):
    if election_type not in CACHE["election_types"]:
        CACHE["election_types"][election_type] = ElectionType.objects.get(
            election_type=election_type
        )
    return CACHE["election_types"][election_type]


def get_cached_election_subtype(election_type):
    if election_type not in CACHE["election_sub_types"]:
        CACHE["election_sub_types"][
            election_type
        ] = ElectionSubType.objects.filter(election_type=election_type)
    return CACHE["election_sub_types"][election_type]


def get_cached_valid_election_types(organisation):
    if organisation not in CACHE["valid_election_types"]:
        CACHE["valid_election_types"][
            organisation
        ] = organisation.election_types.all()
    return CACHE["valid_election_types"][organisation]


def get_cached_private_elections(date, election_id):
    if date not in CACHE["private_elections"]:
        qs = Election.private_objects.filter(poll_open_date=date)
        CACHE["private_elections"][date] = {e.election_id: e for e in qs}
    return CACHE["private_elections"][date].get(election_id)


def get_cached_elected_role(organisation, election_type):
    if election_type not in CACHE["elected_roles"]:
        CACHE["elected_roles"][election_type] = {}

    if organisation not in CACHE["elected_roles"][election_type]:
        try:
            CACHE["elected_roles"][election_type][
                organisation
            ] = ElectedRole.objects.get(
                organisation=organisation, election_type=election_type
            )
        except ElectedRole.DoesNotExist:
            CACHE["elected_roles"][election_type][organisation] = None
    return CACHE["elected_roles"][election_type][organisation]


class ElectionBuilder:
    def __init__(self, election_type, date):
        # init params
        if type(election_type) == str:
            election_type = get_cached_election_type(election_type)
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
        self.seats_contested = None

        # meta-data
        self._use_org = False
        self.notice = None
        self.source = ""
        self.snooped_election_id = None

    def with_subtype(self, subtype):
        valid_subtypes = get_cached_election_subtype(self.election_type)
        if subtype not in valid_subtypes:
            raise ElectionSubType.ValidationError(
                "'%s' is not a valid subtype for election type '%s'"
                % (subtype, self.election_type)
            )

        self.id = self.id.with_subtype(subtype.election_subtype)
        self.subtype = subtype
        return self

    def with_organisation(self, organisation):
        valid_election_types = get_cached_valid_election_types(organisation)
        if self.election_type not in valid_election_types:
            raise Organisation.ValidationError(
                "'%s' is not a valid organisation for election type '%s'"
                % (organisation, self.election_type)
            )

        if organisation.start_date and organisation.start_date > self.date:
            raise Organisation.ValidationError(
                "Organisation start date after election date"
            )
        if organisation.end_date and organisation.end_date < self.date:
            raise Organisation.ValidationError(
                "Organisation end date before election date"
            )

        # if this is a top-level group id
        # we associate the election object with an organisation
        # but the organisation doesn't form part of the id
        if organisation.organisation_type == self.election_type.election_type:
            self._use_org = False
            self.organisation = Organisation.objects.get(
                organisation_type=self.election_type.election_type
            )
        else:
            self._use_org = True
            self.id = self.id.with_organisation(organisation.slug)
            self.organisation = organisation
        return self

    def with_division(self, division):
        if division.organisation != self.organisation:
            raise OrganisationDivision.ValidationError(
                "'%s' is not a child of '%s'" % (division, self.organisation)
            )

        if (
            self.subtype
            and self.subtype.election_subtype
            != division.division_election_sub_type
        ):
            raise OrganisationDivision.ValidationError(
                "election subtype is '%s' but division is of subtype '%s'"
                % (
                    self.subtype.election_subtype,
                    division.division_election_sub_type,
                )
            )

        divisionset = division.divisionset

        if divisionset.start_date and divisionset.start_date > self.date:
            raise OrganisationDivisionSet.ValidationError(
                "DivisionSet start date after election date"
            )
        if divisionset.end_date and divisionset.end_date < self.date:
            raise OrganisationDivisionSet.ValidationError(
                "DivisionSet end date before election date"
            )

        self.id = self.id.with_division(division.slug)
        self.division = division
        return self

    def with_contest_type(self, contest_type):
        self.id = self.id.with_contest_type(contest_type)
        self.contest_type = contest_type
        return self

    def with_seats_contested(self, seats):
        if seats > self.division.seats_total:
            raise ValueError(
                f"Seats contested can't be more than seats total ({seats} > {self.division.seats_total})"
            )
        self.seats_contested = seats
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
        return get_cached_elected_role(
            self.organisation, election_type=self.election_type
        )

    def get_voting_system(self):
        if not self.organisation:
            return None
        return VotingSystemMatcher(
            self.id.ids[-1], nation=self.organisation.territory_code
        ).get_voting_system()

    def get_seats_contested(self):
        if not self.seats_contested:
            return 1
        return self.seats_contested

    def get_seats_total(self):
        if not self.division:
            return None
        return self.division.seats_total

    def __repr__(self):
        return self.id.__repr__()

    def to_title(self, id_type):
        if id_type == "election":
            return self.election_type.name

        parts = []

        if self.subtype:
            subtype_title = "{election} ({subtype})".format(
                election=self.election_type.name, subtype=self.subtype.name
            )
            if id_type == "subtype":
                return subtype_title
            parts.append(subtype_title)

        if self._use_org and self.organisation:
            if self.election_type.election_type == "mayor":
                parts.append(self.get_elected_role().elected_role_name)
            else:
                parts.append(self.organisation.election_name)

        if self.division:
            parts.append(self.division.name)

        if self.contest_type == "by":
            parts.append("by-election")

        return " ".join(parts).strip()

    def __eq__(self, other):
        return self.id.__eq__(other.id)

    def _build(self, record):
        def merge_dicts(d1, d2):
            d3 = d1.copy()
            d3.update(d2)
            return d3

        existing_election = get_cached_private_elections(
            self.date, record["election_id"]
        )
        if existing_election:
            return existing_election
        # return an instance of elections.models.Election
        # but don't persist it to the DB yet.
        # The calling code is responsible for calling .save()
        return Election(
            **merge_dicts(
                record,
                {
                    "poll_open_date": self.date,
                    "election_type": self.election_type,
                    "election_subtype": self.subtype,
                    "organisation": self.organisation,
                    "division": self.division,
                    "elected_role": self.get_elected_role(),
                    "voting_system": self.get_voting_system(),
                },
            )
        )

    def build_election_group(self):
        return self._build(
            {
                "election_id": self.id.election_group_id,
                "election_title": self.to_title("election"),
                "group": None,
                "group_type": "election",
                "notice": None,
                "source": "",
                "snooped_election_id": None,
            }
        )

    def build_subtype_group(self, group, group_type="subtype"):
        return self._build(
            {
                "election_id": self.id.subtype_group_id,
                "election_title": self.to_title("subtype"),
                "group": group,
                "group_type": group_type,
                "notice": None,
                "source": "",
                "snooped_election_id": None,
            }
        )

    def build_organisation_group(self, group):
        return self._build(
            {
                "election_id": self.id.organisation_group_id,
                "election_title": self.to_title("organisation"),
                "group": group,
                "group_type": "organisation",
                "notice": None,
                "source": "",
                "snooped_election_id": None,
            }
        )

    def build_ballot(self, group):
        return self._build(
            {
                "election_id": self.id.ballot_id,
                "election_title": self.to_title("ballot"),
                "group": group,
                "group_type": None,
                "notice": self.notice,
                "source": self.source,
                "snooped_election_id": self.snooped_election_id,
                "seats_contested": self.get_seats_contested(),
                "seats_total": self.get_seats_total(),
            }
        )


def get_or_create_eco_group_metadata():
    return MetaData.objects.get_or_create(
        description="Pre-ECO election",
        defaults={
            "data": {
                "pre_eco": {
                    "title": "This area is expecting a boundary change.",
                    "detail": "Full details of wards will be available soon",
                    "url": None,
                }
            }
        },
    )[0]


def create_ids_for_each_ballot_paper(all_data, subtypes=None):
    all_ids = []
    for organisation in all_data.get("election_organisation", []):
        group_id = None

        div_data = {}
        for form_data in all_data.get("election_divisions", []):
            if (
                form_data["ballot_type"]
                and form_data["ballot_type"] != "no_seats"
            ):
                div_data[form_data["division_id"]] = {
                    "seats_contested": form_data["seats_contested"],
                    "ballot_type": form_data["ballot_type"],
                }

        election_type = all_data["election_type"].election_type
        organisation_type = organisation.organisation_type

        # GROUP 1
        # Make a group ID for the date and election type
        builder = ElectionBuilder(all_data["election_type"], all_data["date"])
        if all_data["election_type"].election_type not in [
            "local",
            "mayor",
            "pcc",
        ]:
            builder.with_organisation(organisation)
        date_id = builder.build_election_group()

        if date_id.election_id not in [e.election_id for e in all_ids]:
            all_ids.append(date_id)

        # GROUP 2
        # Make a group ID for the date, election type and org
        if div_data:
            if election_type != organisation_type:
                group_id = (
                    ElectionBuilder(all_data["election_type"], all_data["date"])
                    .with_organisation(organisation)
                    .build_organisation_group(date_id)
                )
                if group_id.election_id not in [e.election_id for e in all_ids]:
                    all_ids.append(group_id)
            else:
                group_id = date_id

        # Special case where we have no divs for an org that should have them.
        # This is generally due to an upcoming ECO that's not been Made yet.
        # In this case, we want to make an org ID but no div IDs
        if (
            all_data["election_type"].election_type == "local"
            and f"{organisation.pk}_no_divs" in all_data
        ):
            group_id = (
                ElectionBuilder(all_data["election_type"], all_data["date"])
                .with_organisation(organisation)
                .build_organisation_group(date_id)
            )
            group_id.group_type = None
            group_id.metadata = get_or_create_eco_group_metadata()
            all_ids.append(group_id)

        if all_data["election_type"].election_type in ["mayor", "pcc"]:
            group_id = date_id
            mayor_id = (
                ElectionBuilder(all_data["election_type"], all_data["date"])
                .with_organisation(organisation)
                .with_source(all_data.get("source", ""))
                .with_snooped_election(all_data.get("radar_id", None))
                .build_ballot(group_id)
            )
            if mayor_id.election_id not in [e.election_id for e in all_ids]:
                all_ids.append(mayor_id)

        if subtypes:
            for subtype in subtypes:
                # Special case `gla.a` elections as they should be a ballot
                if (
                    organisation.slug == "gla"
                    and subtype.election_subtype == "a"
                ):
                    group_id = date_id
                    group_type = None
                else:
                    group_type = "subtype"
                subtype_id = (
                    ElectionBuilder(all_data["election_type"], all_data["date"])
                    .with_organisation(organisation)
                    .with_source(all_data.get("source", ""))
                    .with_snooped_election(all_data.get("radar_id", None))
                    .with_subtype(subtype)
                    .build_subtype_group(group_id, group_type=group_type)
                )
                if subtype_id.election_id not in [
                    e.election_id for e in all_ids
                ]:
                    all_ids.append(subtype_id)

                for div_id, div_details in div_data.items():
                    contest_type = div_details["ballot_type"]
                    try:
                        org_div = OrganisationDivision.objects.get(
                            pk=div_id,
                            division_election_sub_type=subtype.election_subtype,
                        )
                    except OrganisationDivision.DoesNotExist:
                        # This (id, subtype) pair doesn't exist.
                        # That's ok, as we're looping through all subtypes,
                        # so we'll make an election for this division soon
                        continue

                    builder = (
                        ElectionBuilder(
                            all_data["election_type"], all_data["date"]
                        )
                        .with_subtype(subtype)
                        .with_organisation(organisation)
                        .with_division(org_div)
                        .with_source(all_data.get("source", ""))
                        .with_snooped_election(all_data.get("radar_id", None))
                    )

                    if contest_type == "by_election":
                        all_ids.append(
                            builder.with_contest_type("by").build_ballot(
                                subtype_id
                            )
                        )
                    elif contest_type in ["contested", "seats_contested"]:
                        all_ids.append(builder.build_ballot(subtype_id))
                    else:
                        raise ValueError(
                            "Unrecognised contest_type value '%s'"
                            % contest_type
                        )
        else:
            all_division_ids = div_data.keys()
            all_division_objects = {
                str(div.pk): div
                for div in OrganisationDivision.objects.filter(
                    pk__in=all_division_ids,
                    divisionset__organisation=organisation,
                ).select_related(
                    "divisionset",
                    "divisionset__organisation",
                )
            }
            for div_id, division in all_division_objects.items():
                ballot_data = div_data[div_id]
                contest_type = ballot_data["ballot_type"]
                org_div = all_division_objects[str(div_id)]

                builder = (
                    ElectionBuilder(all_data["election_type"], all_data["date"])
                    .with_organisation(organisation)
                    .with_division(org_div)
                    .with_source(all_data.get("source", ""))
                    .with_snooped_election(all_data.get("radar_id", None))
                    .with_seats_contested(ballot_data["seats_contested"])
                )

                if contest_type == "by_election":
                    all_ids.append(
                        builder.with_contest_type("by").build_ballot(group_id)
                    )
                elif contest_type in ["contested", "seats_contested"]:
                    all_ids.append(builder.build_ballot(group_id))
                else:
                    raise ValueError(
                        "Unrecognised contest_type value '%s'" % contest_type
                    )
    return all_ids


def get_notice_directory(elections):
    """
    given a list of Election objects work out a
    sensible place to store the notice of election doc
    """

    election_group_id = ""
    organisation_group_id = ""
    ballot_id = ""
    ballot_count = 0
    for election in elections:
        if election.group_type == "election":
            election_group_id = election.election_id
        elif election.group_type == "organisation":
            organisation_group_id = election.election_id
        elif not election.group_type:
            ballot_id = election.election_id if ballot_count == 0 else ""
            ballot_count = ballot_count + 1
        else:
            raise ValueError(
                "unrecognised Election group_type '%s'" % (election.group_type)
            )

    if ballot_count == 1 and ballot_id:
        return ballot_id
    if organisation_group_id:
        return organisation_group_id
    if election_group_id:
        return election_group_id

    # if we get here, something went wrong
    # the function might have been called with an empty list
    raise ValueError("Can't find an appropriate election id")
    if ballot_count == 1 and ballot_id:
        return ballot_id
    if organisation_group_id:
        return organisation_group_id
    if election_group_id:
        return election_group_id

    # if we get here, something went wrong
    # the function might have been called with an empty list
    raise ValueError("Can't find an appropriate election id")
