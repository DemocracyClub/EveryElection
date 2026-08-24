from datetime import date

from organisations.tests.factories import (
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
    OrganisationFactory,
    OrganisationGeographyFactory,
)
from rest_framework.test import APITestCase


class TestOrganisationAPIEndpoint(APITestCase):
    def setUp(self):
        super().setUp()
        OrganisationGeographyFactory(
            organisation=OrganisationFactory(
                official_identifier="TEST1",
                official_name="Foo & Bar District Council",
                organisation_type="local-authority",
                start_date=date(2016, 10, 1),
                end_date=date(2017, 10, 1),
            )
        )
        OrganisationFactory(
            official_identifier="TEST1",
            official_name="Bar with Foo District Council",
            organisation_type="local-authority",
            start_date=date(2017, 10, 2),
            end_date=None,
        )

        OrganisationFactory(
            official_identifier="TEST2",
            official_name="Baz District Council",
            organisation_type="local-authority",
            start_date=date(2016, 10, 1),
            end_date=date(2017, 10, 1),
        )

    def test_get_org_valid(self):
        resp = self.client.get(
            "/api/organisations/local-authority/TEST1/2016-10-01.json"
        )
        data = resp.json()
        self.assertEqual(200, resp.status_code)
        self.assertEqual("Foo & Bar District Council", data["official_name"])

    def test_get_org_not_found(self):
        resp = self.client.get(
            "/api/organisations/local-authority/TEST1/2001-10-01.json"
        )
        self.assertEqual(404, resp.status_code)

    def test_get_org_geo_valid(self):
        resp = self.client.get(
            "/api/organisations/local-authority/TEST1/2016-10-01/geo.json"
        )
        data = resp.json()
        self.assertEqual(200, resp.status_code)
        self.assertEqual(
            "Foo & Bar District Council", data["properties"]["official_name"]
        )

    def test_get_org_geo_not_found(self):
        resp = self.client.get(
            "/api/organisations/local-authority/TEST1/2001-10-01/geo.json"
        )
        self.assertEqual(404, resp.status_code)

    def test_filter_orgs_type_valid(self):
        resp = self.client.get("/api/organisations/local-authority.json")
        data = resp.json()
        self.assertEqual(200, resp.status_code)
        self.assertEqual(3, data["count"])

    def test_filter_orgs_type_not_found(self):
        resp = self.client.get("/api/organisations/not-a-thing.json")
        data = resp.json()
        self.assertEqual(200, resp.status_code)
        self.assertEqual([], data["results"])

    def test_filter_orgs_type_id_valid(self):
        resp = self.client.get("/api/organisations/local-authority/TEST1.json")
        data = resp.json()
        self.assertEqual(200, resp.status_code)
        self.assertEqual(2, data["count"])

    def test_filter_orgs_type_id_not_found(self):
        resp = self.client.get("/api/organisations/local-authority/TEST3.json")
        data = resp.json()
        self.assertEqual(200, resp.status_code)
        self.assertEqual([], data["results"])


class TestOrganisationDivisionSetFields(APITestCase):
    def setUp(self):
        super().setUp()
        self.org = OrganisationFactory(
            official_identifier="STR",
            organisation_type="local-authority",
            start_date=date(2019, 4, 1),
            end_date=None,
        )
        self.active_ds = OrganisationDivisionSetFactory(
            organisation=self.org,
            start_date=date(2019, 5, 2),
            end_date=None,
            short_title="Stroud 2019 Review",
        )
        OrganisationDivisionFactory(divisionset=self.active_ds)
        OrganisationDivisionFactory(divisionset=self.active_ds)

        self.org_url = "/api/organisations/local-authority/STR/2019-04-01.json"

    def test_response_includes_divisionset_keys(self):
        resp = self.client.get(self.org_url)
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertIn("current_divisionset", data)
        self.assertIn("divisionsets_url", data)

    def test_current_divisionset_non_null_for_active_org(self):
        resp = self.client.get(self.org_url)
        data = resp.json()
        self.assertIsNotNone(data["current_divisionset"])
        self.assertEqual(
            "Stroud 2019 Review", data["current_divisionset"]["short_title"]
        )
        self.assertIsNone(data["current_divisionset"]["end_date"])

    def test_current_divisionset_null_when_all_historical(self):
        org2 = OrganisationFactory(
            official_identifier="OLD",
            organisation_type="local-authority",
            start_date=date(2010, 1, 1),
            end_date=None,
        )
        OrganisationDivisionSetFactory(
            organisation=org2,
            start_date=date(2010, 1, 1),
            end_date=date(2019, 1, 1),
        )
        resp = self.client.get(
            "/api/organisations/local-authority/OLD/2010-01-01.json"
        )
        data = resp.json()
        self.assertIsNone(data["current_divisionset"])

    def test_current_divisionset_division_count(self):
        resp = self.client.get(self.org_url)
        data = resp.json()
        self.assertEqual(2, data["current_divisionset"]["division_count"])

    def test_divisionsets_url_contains_org_slug(self):
        resp = self.client.get(self.org_url)
        data = resp.json()
        self.assertIn(f"?org_slug={self.org.slug}", data["divisionsets_url"])
        self.assertTrue(data["divisionsets_url"].startswith("http"))
