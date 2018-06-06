from datetime import date
from rest_framework.test import APITestCase
from organisations.tests.factories import OrganisationFactory


class TestOrganisationAPIEndpoint(APITestCase):

    def setUp(self):
        super().setUp()
        OrganisationFactory(
            official_identifier='TEST1',
            official_name='Foo & Bar District Council',
            organisation_type = "local-authority",
            start_date=date(2016, 10, 1),
            end_date=date(2017, 10, 1)
        )
        OrganisationFactory(
            official_identifier='TEST1',
            official_name='Bar with Foo District Council',
            organisation_type = "local-authority",
            start_date=date(2017, 10, 2),
            end_date=None
        )

        OrganisationFactory(
            official_identifier='TEST2',
            official_name='Baz District Council',
            organisation_type = "local-authority",
            start_date=date(2016, 10, 1),
            end_date=date(2017, 10, 1)
        )


    def test_get_org_valid(self):
        resp = self.client.get("/api/organisations/local-authority/TEST1/2016-10-01.json")
        data = resp.json()
        self.assertEqual(200, resp.status_code)
        self.assertEqual('Foo & Bar District Council', data['official_name'])

    def test_get_org_not_found(self):
        resp = self.client.get("/api/organisations/local-authority/TEST1/2001-10-01.json")
        self.assertEqual(404, resp.status_code)

    def test_filter_orgs_valid(self):
        resp = self.client.get("/api/organisations/local-authority/TEST1.json")
        data = resp.json()
        self.assertEqual(200, resp.status_code)
        self.assertEqual(2, len(data))

    def test_filter_orgs_not_found(self):
        resp = self.client.get("/api/organisations/local-authority/TEST3.json")
        data = resp.json()
        self.assertEqual(200, resp.status_code)
        self.assertEqual([], data)
