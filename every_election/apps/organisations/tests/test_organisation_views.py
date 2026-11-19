from datetime import date

from django.test import TestCase
from organisations.tests.factories import OrganisationFactory


class TestOrganisationDetailView(TestCase):
    @classmethod
    def setUpTestData(cls):
        OrganisationFactory(
            official_identifier="TEST1",
            organisation_type="local-authority",
            start_date=date(2016, 10, 1),
        )

    def test_impossible_date_not_found(self):
        resp = self.client.get(
            "/organisations/local-authority/TEST1/2016-13-45/"
        )
        self.assertEqual(404, resp.status_code)
