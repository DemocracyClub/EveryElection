from datetime import date

from django.test import override_settings
from organisations.tests.factories import (
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
    OrganisationFactory,
)
from rest_framework.test import APITestCase


class TestDivisionsEndpoint(APITestCase):
    def setUp(self):
        super().setUp()
        self.local_org = OrganisationFactory(
            official_identifier="STR",
            organisation_type="local-authority",
            start_date=date(2019, 4, 1),
            end_date=None,
        )
        self.active_ds = OrganisationDivisionSetFactory(
            organisation=self.local_org,
            start_date=date(2019, 5, 2),
            end_date=None,
            short_title="Stroud 2019 Review",
        )
        self.historical_ds = OrganisationDivisionSetFactory(
            organisation=self.local_org,
            start_date=date(2010, 1, 1),
            end_date=date(2019, 5, 1),
            short_title="Stroud 2010 Review",
        )
        self.division_active = OrganisationDivisionFactory(
            divisionset=self.active_ds,
            name="Amberley",
        )
        self.division_historical = OrganisationDivisionFactory(
            divisionset=self.historical_ds,
            name="Old Ward",
        )

        self.other_org = OrganisationFactory(
            official_identifier="PCC1",
            organisation_type="combined-authority",
            start_date=date(2017, 1, 1),
            end_date=None,
        )
        self.other_ds = OrganisationDivisionSetFactory(
            organisation=self.other_org,
            start_date=date(2017, 1, 1),
            end_date=None,
        )
        self.other_division = OrganisationDivisionFactory(
            divisionset=self.other_ds,
            name="Other Division",
        )

    def test_list_returns_200_with_pagination(self):
        resp = self.client.get("/api/divisions/")
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertIn("count", data)
        self.assertIn("results", data)

    def test_list_result_shape(self):
        resp = self.client.get("/api/divisions/")
        data = resp.json()
        result = data["results"][0]
        self.assertIn("divisionset", result)
        self.assertIn("organisation", result)
        self.assertIn("name", result)

    def test_filter_by_org_type(self):
        resp = self.client.get("/api/divisions/?org_type=local-authority")
        data = resp.json()
        org_types = {
            r["organisation"]["organisation_type"] for r in data["results"]
        }
        self.assertEqual({"local-authority"}, org_types)

    def test_filter_by_org_slug(self):
        resp = self.client.get(
            f"/api/divisions/?org_slug={self.local_org.slug}"
        )
        data = resp.json()
        slugs = {r["organisation"]["slug"] for r in data["results"]}
        self.assertEqual({self.local_org.slug}, slugs)
        # should include both active and historical divisionset divisions
        self.assertEqual(2, data["count"])

    def test_filter_current_excludes_historical(self):
        resp = self.client.get("/api/divisions/?current=true")
        data = resp.json()
        for result in data["results"]:
            self.assertIsNone(result["divisionset"]["end_date"])

    def test_detail_endpoint(self):
        resp = self.client.get(f"/api/divisions/{self.division_active.pk}/")
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertEqual("Amberley", data["name"])
        self.assertIn("divisionset", data)
        self.assertIn("organisation", data)
        self.assertEqual("STR", data["organisation"]["official_identifier"])

    @override_settings(DEBUG=False)
    def test_query_count_select_related(self):
        for i in range(10):
            OrganisationDivisionFactory(divisionset=self.active_ds)

        # With select_related, one query for count + one for data (no per-row extras)
        with self.assertNumQueries(2):
            self.client.get("/api/divisions/?limit=10")
