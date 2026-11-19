from datetime import date

from organisations.tests.factories import (
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
    OrganisationFactory,
)
from rest_framework.test import APITestCase

ORG_URL = "/api/organisations/local-authority/TEST1/2016-10-01"
SP_ORG_URL = "/api/organisations/sp/sp/1999-05-06"
HOST = "http://testserver"


class DivisionSetAPITestCase(APITestCase):
    """
    A local authority (TEST1) with three consecutive division sets:
        old:     2016-10-01 to 2019-05-01
        current: 2019-05-02 to 2027-05-05
        future:  2027-05-06 onwards


    The Scottish Parliament (sp) with one division set, starting
    2011-05-05, which has divisions of two types:
        constituencies (SPC)
        regions (SPE).
    """

    @classmethod
    def setUpTestData(cls):
        cls.org = OrganisationFactory(
            official_identifier="TEST1",
            organisation_type="local-authority",
            common_name="Test One",
            start_date=date(2016, 10, 1),
            end_date=None,
        )
        cls.old_divset = OrganisationDivisionSetFactory(
            organisation=cls.org,
            start_date="2016-10-01",
            end_date="2019-05-01",
            short_title="Old divisions",
        )
        cls.current_divset = OrganisationDivisionSetFactory(
            organisation=cls.org,
            start_date="2019-05-02",
            end_date="2027-05-05",
            short_title="Current divisions",
        )
        cls.future_divset = OrganisationDivisionSetFactory(
            organisation=cls.org,
            start_date="2027-05-06",
            end_date=None,
            short_title="Future divisions",
        )
        for name in ["Ward B", "Ward A"]:
            OrganisationDivisionFactory(
                divisionset=cls.current_divset,
                name=name,
                division_type="DIW",
            )

        cls.sp_org = OrganisationFactory(
            official_identifier="sp",
            organisation_type="sp",
            common_name="Scottish Parliament",
            start_date=date(1999, 5, 6),
            end_date=None,
        )
        cls.sp_divset = OrganisationDivisionSetFactory(
            organisation=cls.sp_org,
            start_date="2011-05-05",
            end_date=None,
            short_title="Scottish Parliament divisions",
        )
        for name, division_type in [
            ("Glasgow Kelvin", "SPC"),
            ("Edinburgh Central", "SPC"),
            ("Lothian", "SPE"),
        ]:
            OrganisationDivisionFactory(
                divisionset=cls.sp_divset,
                name=name,
                division_type=division_type,
            )


class TestDivisionSetDetail(DivisionSetAPITestCase):
    def test_detail(self):
        resp = self.client.get(f"{ORG_URL}/division_sets/2019-05-02/")
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertEqual(
            [
                "url",
                "start_date",
                "end_date",
                "short_title",
                "legislation_url",
                "consultation_url",
                "notes",
                "division_types",
                "previous",
                "next",
                "divisions",
            ],
            list(data.keys()),
        )
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2019-05-02/", data["url"]
        )
        self.assertEqual("2019-05-02", data["start_date"])
        self.assertEqual("2027-05-05", data["end_date"])
        self.assertEqual("Current divisions", data["short_title"])
        self.assertEqual(["DIW"], data["division_types"])
        self.assertEqual(
            ["Ward A", "Ward B"],
            [division["name"] for division in data["divisions"]],
        )
        self.assertEqual(
            [
                "name",
                "official_identifier",
                "slug",
                "division_type",
                "division_subtype",
                "division_election_sub_type",
                "seats_total",
                "territory_code",
                "created",
                "modified",
            ],
            list(data["divisions"][0].keys()),
        )

    def test_previous_and_next(self):
        data = self.client.get(f"{ORG_URL}/division_sets/2019-05-02/").json()
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2016-10-01/", data["previous"]
        )
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2027-05-06/", data["next"]
        )

    def test_previous_and_next_at_ends(self):
        first = self.client.get(f"{ORG_URL}/division_sets/2016-10-01/").json()
        self.assertIsNone(first["previous"])
        self.assertIsNotNone(first["next"])
        last = self.client.get(f"{ORG_URL}/division_sets/2027-05-06/").json()
        self.assertIsNotNone(last["previous"])
        self.assertIsNone(last["next"])

    def test_previous_and_next_ignore_other_organisations(self):
        OrganisationDivisionSetFactory(
            organisation=OrganisationFactory(official_identifier="TEST2"),
            start_date="2000-01-01",
            end_date=None,
        )
        first = self.client.get(f"{ORG_URL}/division_sets/2016-10-01/").json()
        self.assertIsNone(first["previous"])

    def test_format_suffix(self):
        resp = self.client.get(f"{ORG_URL}/division_sets/2019-05-02.json")
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2019-05-02.json", data["url"]
        )
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2027-05-06.json", data["next"]
        )

    def test_dates_match_within_lifetime(self):
        """
        Neither date in the URL has to be a start date, but the URLs in
        the response always use the start dates.
        """
        resp = self.client.get(
            "/api/organisations/local-authority/TEST1/2024-01-01/division_sets/2025-06-15/"
        )
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertEqual("Current divisions", data["short_title"])
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2019-05-02/", data["url"]
        )

    def test_end_date_is_inclusive(self):
        data = self.client.get(f"{ORG_URL}/division_sets/2027-05-05/").json()
        self.assertEqual("Current divisions", data["short_title"])

    def test_open_ended_division_set(self):
        data = self.client.get(f"{ORG_URL}/division_sets/2099-01-01/").json()
        self.assertEqual("Future divisions", data["short_title"])

    def test_date_before_first_division_set_not_found(self):
        resp = self.client.get(f"{ORG_URL}/division_sets/2001-01-01/")
        self.assertEqual(404, resp.status_code)

    def test_organisation_not_found(self):
        resp = self.client.get(
            "/api/organisations/local-authority/NOPE/2016-10-01/division_sets/2019-05-02/"
        )
        self.assertEqual(404, resp.status_code)

    def test_impossible_dates_not_found(self):
        # Each request uses a different date so the message shows which
        # URL segment was rejected.
        resp = self.client.get(f"{ORG_URL}/division_sets/2019-13-45/")
        self.assertEqual(404, resp.status_code)
        self.assertEqual(
            "'2019-13-45' is not a valid yyyy-mm-dd date", resp.json()["detail"]
        )
        resp = self.client.get(
            "/api/organisations/local-authority/TEST1/2016-02-30/division_sets/2019-05-02/"
        )
        self.assertEqual(404, resp.status_code)
        self.assertEqual(
            "'2016-02-30' is not a valid yyyy-mm-dd date", resp.json()["detail"]
        )

    def test_provisional_organisation_not_found(self):
        org = OrganisationFactory(official_identifier="PROV", provisional=True)
        OrganisationDivisionSetFactory(
            organisation=org, start_date="2017-01-01", end_date=None
        )
        resp = self.client.get(
            "/api/organisations/local-authority/PROV/2016-10-01/division_sets/2017-01-01/"
        )
        self.assertEqual(404, resp.status_code)

    def test_multiple_division_types(self):
        data = self.client.get(f"{SP_ORG_URL}/division_sets/2011-05-05/").json()
        self.assertEqual(["SPC", "SPE"], data["division_types"])
        self.assertEqual(
            ["Edinburgh Central", "Glasgow Kelvin", "Lothian"],
            [division["name"] for division in data["divisions"]],
        )

    def test_filter_divisions_by_type(self):
        data = self.client.get(
            f"{SP_ORG_URL}/division_sets/2011-05-05/?division_type=SPC"
        ).json()
        self.assertEqual(
            ["Edinburgh Central", "Glasgow Kelvin"],
            [division["name"] for division in data["divisions"]],
        )
        # division_types describes the whole division set
        self.assertEqual(["SPC", "SPE"], data["division_types"])

    def test_filter_divisions_by_type_no_match(self):
        resp = self.client.get(
            f"{ORG_URL}/division_sets/2019-05-02/?division_type=nope"
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual([], resp.json()["divisions"])

    def test_query_count(self):
        # organisation, division set, division types, previous, next,
        # divisions
        with self.assertNumQueries(6):
            self.client.get(f"{ORG_URL}/division_sets/2019-05-02/")


SUMMARY_FIELDS = [
    "url",
    "start_date",
    "end_date",
    "short_title",
    "legislation_url",
    "consultation_url",
    "notes",
]


class TestDivisionSetOrganisationList(DivisionSetAPITestCase):
    def test_list(self):
        # A division set belonging to a different organisation,
        # which should not be listed
        OrganisationDivisionSetFactory(
            organisation=OrganisationFactory(official_identifier="TEST2")
        )

        resp = self.client.get(f"{ORG_URL}/division_sets/")
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertEqual(
            ["count", "next", "previous", "results"], list(data.keys())
        )
        self.assertEqual(3, data["count"])
        self.assertEqual(
            ["Future divisions", "Current divisions", "Old divisions"],
            [result["short_title"] for result in data["results"]],
        )
        self.assertEqual(SUMMARY_FIELDS, list(data["results"][0].keys()))
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2027-05-06/",
            data["results"][0]["url"],
        )

    def test_format_suffix(self):
        resp = self.client.get(f"{ORG_URL}/division_sets.json")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(3, resp.json()["count"])

    def test_organisation_date_matches_within_lifetime(self):
        resp = self.client.get(
            "/api/organisations/local-authority/TEST1/2024-01-01/division_sets/"
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(3, resp.json()["count"])

    def test_only_lists_one_generation_of_an_organisation(self):
        self.org.end_date = date(2030, 1, 1)
        self.org.save()
        self.future_divset.end_date = date(2030, 1, 1)
        self.future_divset.save()
        next_generation = OrganisationFactory(
            official_identifier="TEST1",
            organisation_type="local-authority",
            start_date=date(2030, 1, 2),
        )
        OrganisationDivisionSetFactory(
            organisation=next_generation,
            start_date="2030-01-02",
            end_date=None,
            short_title="Next generation divisions",
        )
        data = self.client.get(
            "/api/organisations/local-authority/TEST1/2030-01-02/division_sets/"
        ).json()
        self.assertEqual(
            ["Next generation divisions"],
            [result["short_title"] for result in data["results"]],
        )

    def test_organisation_without_division_sets(self):
        OrganisationFactory(official_identifier="TEST2")
        resp = self.client.get(
            "/api/organisations/local-authority/TEST2/2016-10-01/division_sets/"
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual([], resp.json()["results"])

    def test_organisation_not_found(self):
        resp = self.client.get(
            "/api/organisations/local-authority/NOPE/2016-10-01/division_sets/"
        )
        self.assertEqual(404, resp.status_code)

    def test_provisional_organisation_not_found(self):
        OrganisationFactory(official_identifier="PROV", provisional=True)
        resp = self.client.get(
            "/api/organisations/local-authority/PROV/2016-10-01/division_sets/"
        )
        self.assertEqual(404, resp.status_code)

    def test_query_count(self):
        # organisation, count, division sets
        with self.assertNumQueries(3):
            self.client.get(f"{ORG_URL}/division_sets/")
