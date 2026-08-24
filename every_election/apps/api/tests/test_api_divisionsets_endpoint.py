from datetime import date, timedelta

from organisations.tests.factories import (
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
    OrganisationFactory,
)
from rest_framework.test import APITestCase


class TestDivisionSetsEndpoint(APITestCase):
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
        self.div1 = OrganisationDivisionFactory(
            divisionset=self.active_ds,
            name="Amberley",
            official_identifier="gss:E05013500",
        )
        self.div2 = OrganisationDivisionFactory(
            divisionset=self.active_ds,
            name="Bisley",
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

    def test_list_returns_200(self):
        resp = self.client.get("/api/divisionsets/")
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertIn("count", data)
        self.assertIn("results", data)

    def test_result_shape(self):
        resp = self.client.get(f"/api/divisionsets/{self.active_ds.pk}/")
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertIn("url", data)
        self.assertIn("organisation", data)
        self.assertIn("start_date", data)
        self.assertIn("end_date", data)
        self.assertIn("short_title", data)
        self.assertIn("divisions", data)

    def test_organisation_fields_on_divisionset(self):
        resp = self.client.get(f"/api/divisionsets/{self.active_ds.pk}/")
        data = resp.json()
        org = data["organisation"]
        self.assertEqual("STR", org["official_identifier"])
        self.assertEqual("local-authority", org["organisation_type"])
        self.assertIn("url", org)

    def test_divisions_embedded_in_divisionset(self):
        resp = self.client.get(f"/api/divisionsets/{self.active_ds.pk}/")
        data = resp.json()
        self.assertEqual(2, len(data["divisions"]))
        division = next(d for d in data["divisions"] if d["name"] == "Amberley")
        self.assertIn("geo_url", division)
        self.assertIn("geography_url", division)

    def test_division_geo_url_points_to_divisions_endpoint(self):
        resp = self.client.get(f"/api/divisionsets/{self.active_ds.pk}/")
        data = resp.json()
        division = next(d for d in data["divisions"] if d["name"] == "Amberley")
        self.assertIn(f"/api/divisions/{self.div1.pk}/geo", division["geo_url"])

    def test_division_geography_url_is_mapit_link_for_gss(self):
        resp = self.client.get(f"/api/divisionsets/{self.active_ds.pk}/")
        data = resp.json()
        division = next(d for d in data["divisions"] if d["name"] == "Amberley")
        self.assertIn("mapit.mysociety.org", division["geography_url"])

    def test_filter_by_official_identifier(self):
        resp = self.client.get("/api/divisionsets/?official_identifier=STR")
        data = resp.json()
        self.assertEqual(2, data["count"])
        for result in data["results"]:
            self.assertEqual(
                "STR", result["organisation"]["official_identifier"]
            )

    def test_filter_by_start_date(self):
        resp = self.client.get("/api/divisionsets/?start_date=2019-05-02")
        data = resp.json()
        self.assertEqual(1, data["count"])
        self.assertEqual("2019-05-02", data["results"][0]["start_date"])

    def test_filter_current_excludes_historical(self):
        resp = self.client.get("/api/divisionsets/?current=true")
        data = resp.json()
        for result in data["results"]:
            self.assertIsNone(result["end_date"])

    def test_filter_current_includes_future_end_date(self):
        future_org = OrganisationFactory(
            official_identifier="FUT",
            organisation_type="local-authority",
            start_date=date(2020, 1, 1),
            end_date=None,
        )
        future_ds = OrganisationDivisionSetFactory(
            organisation=future_org,
            start_date=date(2020, 1, 1),
            end_date=date.today() + timedelta(days=30),
        )
        resp = self.client.get("/api/divisionsets/?current=true")
        data = resp.json()
        ids = [r["url"] for r in data["results"]]
        self.assertTrue(any(str(future_ds.pk) in u for u in ids))

    def test_detail_url_is_absolute(self):
        resp = self.client.get(f"/api/divisionsets/{self.active_ds.pk}/")
        data = resp.json()
        self.assertTrue(data["url"].startswith("http"))
        self.assertIn(str(self.active_ds.pk), data["url"])
