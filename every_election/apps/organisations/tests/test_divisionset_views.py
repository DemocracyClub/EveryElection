from datetime import date

from django.test import TestCase, override_settings
from django.urls import reverse
from organisations.tests.factories import (
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
    OrganisationFactory,
)

ORG_URL = "/organisations/local-authority/TEST1/2016-10-01"


class DivisionSetViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = OrganisationFactory(
            official_identifier="TEST1",
            organisation_type="local-authority",
            start_date=date(2016, 10, 1),
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
            end_date=None,
            short_title="Current divisions",
        )
        OrganisationDivisionFactory(
            divisionset=cls.current_divset, name="Ward A"
        )


class TestDivisionsetDetailView(DivisionSetViewTestCase):
    def test_get_absolute_url(self):
        self.assertEqual(
            f"{ORG_URL}/division_sets/2019-05-02/",
            self.current_divset.get_absolute_url(),
        )

    def test_detail_page(self):
        resp = self.client.get(f"{ORG_URL}/division_sets/2019-05-02/")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(self.current_divset, resp.context["divisionset"])
        self.assertContains(resp, "Current divisions")
        self.assertContains(resp, "Ward A")

    def test_dates_match_within_lifetime(self):
        resp = self.client.get(
            "/organisations/local-authority/TEST1/2024-01-01/division_sets/2018-06-15/"
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(self.old_divset, resp.context["divisionset"])

    def test_not_found(self):
        for url in [
            # before the first division set
            f"{ORG_URL}/division_sets/2001-01-01/",
            # no such organisation
            "/organisations/local-authority/NOPE/2016-10-01/division_sets/2019-05-02/",
            # not dates
            f"{ORG_URL}/division_sets/2019-13-45/",
            "/organisations/local-authority/TEST1/2019-13-45/division_sets/2019-05-02/",
        ]:
            with self.subTest(url=url):
                self.assertEqual(404, self.client.get(url).status_code)

    def test_provisional_organisation(self):
        """
        Division sets of provisional organisations were viewable at
        their primary-key URL, so they still are at the new one.
        """
        divset = OrganisationDivisionSetFactory(
            organisation=OrganisationFactory(
                official_identifier="PROV", provisional=True
            ),
        )
        resp = self.client.get(divset.get_absolute_url())
        self.assertEqual(200, resp.status_code)

    def test_organisation_page_links_to_division_sets(self):
        resp = self.client.get(f"{ORG_URL}/")
        self.assertContains(resp, f'href="{ORG_URL}/division_sets/2019-05-02/"')
        self.assertContains(resp, f'href="{ORG_URL}/division_sets/2016-10-01/"')


class TestDivisionsetRedirectView(DivisionSetViewTestCase):
    def test_primary_key_url_redirects(self):
        resp = self.client.get(
            f"/organisations/divisionsets/{self.current_divset.pk}/"
        )
        self.assertRedirects(
            resp,
            f"{ORG_URL}/division_sets/2019-05-02/",
            status_code=302,
        )

    def test_unknown_primary_key(self):
        resp = self.client.get("/organisations/divisionsets/999999/")
        self.assertEqual(404, resp.status_code)

    def test_non_numeric_primary_key(self):
        resp = self.client.get("/organisations/divisionsets/abc/")
        self.assertEqual(404, resp.status_code)


class TestPMTilesViewInProduction(DivisionSetViewTestCase):
    @override_settings(PUBLIC_DATA_BUCKET="test-bucket")
    def test_redirects_to_detail_page(self):
        """
        When there is a public bucket the files are served from S3, and
        this view sends people to the division set's page instead.
        """
        resp = self.client.get(
            reverse("pmtiles_view", args=[self.current_divset.pk])
        )
        self.assertRedirects(
            resp,
            f"{ORG_URL}/division_sets/2019-05-02/",
            fetch_redirect_response=False,
        )

    @override_settings(PUBLIC_DATA_BUCKET="test-bucket")
    def test_unknown_division_set(self):
        resp = self.client.get(reverse("pmtiles_view", args=[999999]))
        self.assertEqual(404, resp.status_code)
