from api.serializers import (
    ElectionTypeSerializer,
    OrganisationDivisionSerializer,
    OrganisationSerializer,
)
from django.test import RequestFactory
from elections.tests.factories import (
    ElectedRoleFactory,
    ElectionFactory,
    ElectionTypeFactory,
)
from organisations.tests.factories import (
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
    OrganisationFactory,
)


def get_local_ballot():
    """
    Should be everything we need to pass to `ElectionSyncer.add_single_election()`

    """
    factory = RequestFactory()
    request = factory.get("/api/")
    local_organisation = OrganisationFactory(
        official_identifier="REI",
        official_name="Reigate and Banstead Borough Council",
        common_name="Reigate and Banstead",
        slug="reigate-and-banstead",
    )
    local_organisation.save()

    org_dict = OrganisationSerializer(
        local_organisation, context={"request": request}
    ).data

    election_type = ElectionTypeFactory(
        **{"name": "Local elections", "election_type": "local"}
    )
    elected_role = ElectedRoleFactory(
        elected_title="Local Councillor",
        organisation=local_organisation,
        election_type=election_type,
    )

    local_election = ElectionFactory(
        election_id="local.reigate-and-banstead.2022-05-05",
        elected_role=elected_role,
        organisation=local_organisation,
    )

    divisionset_kwargs = {
        "start_date": "2019-05-02",
        "end_date": None,
        "legislation_url": "http://www.legislation.gov.uk/uksi/2019/125/contents/made",
        "consultation_url": "http://www.lgbce.org.uk/all-reviews/south-east/surrey/reigate-and-banstead",
        "short_title": "The Reigate and Banstead (Electoral Changes) Order 2019",
    }
    divisionset = OrganisationDivisionSetFactory(
        organisation=local_organisation,
        **divisionset_kwargs,
    )
    division = OrganisationDivisionFactory(
        divisionset=divisionset,
        **{
            "name": "Banstead Village",
            "official_identifier": "gss:E05012872",
            "slug": "banstead-village",
            "division_type": "DIW",
            "division_subtype": "",
            "division_election_sub_type": "",
            "seats_total": 3,
            "territory_code": "ENG",
            "created": "2019-05-02T00:00:00Z",
            "modified": "2023-03-13T14:02:05.475338Z",
        },
    )

    return {
        "election_id": "local.reigate-and-banstead.banstead-village.2022-05-05",
        "tmp_election_id": None,
        "election_title": "Reigate and Banstead local election Banstead Village",
        "poll_open_date": "2022-05-05",
        "election_type": ElectionTypeSerializer(
            election_type, context={"request": request}
        ).data,
        "election_subtype": None,
        "organisation": org_dict,
        "group": local_election.election_id,
        "group_type": None,
        "identifier_type": "ballot",
        "children": [],
        "elected_role": elected_role.elected_title,
        "seats_contested": 1,
        "division": OrganisationDivisionSerializer(
            division, context={"request": request}
        ).data,
        "voting_system": {
            "name": "First-past-the-post",
            "wikipedia_url": "https://en.m.wikipedia.org/wiki/First-past-the-post_voting",
            "description": "A first-past-the-post (abbreviated FPTP, 1stP, 1PTP or FPP) or winner-takes-all election is one that is won by the candidate receiving more votes than any others.",
            "uses_party_lists": False,
            "slug": "FPTP",
        },
        "requires_voter_id": None,
        "current": False,
        "explanation": None,
        "metadata": None,
        "deleted": False,
        "cancelled": False,
        "cancellation_reason": None,
        "replaces": None,
        "replaced_by": None,
        "tags": {"NUTS1": {"key": "UKJ", "value": "South East (England)"}},
        "created": "2022-01-06T13:43:03.300302Z",
        "modified": "2023-03-15T14:05:49.642005Z",
    }
