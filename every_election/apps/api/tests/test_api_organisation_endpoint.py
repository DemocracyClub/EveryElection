from datetime import date

from organisations.tests.factories import (
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
