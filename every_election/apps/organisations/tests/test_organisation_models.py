from datetime import date
from django.test import TestCase
from organisations.models import Organisation
from organisations.tests.factories import OrganisationFactory


class TestOrganisationManager(TestCase):

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
        OrganisationFactory(
            official_identifier='TEST2',
            official_name='Baz Metropolitan Borough Council',
            organisation_type = "local-authority",
            start_date=date(2017, 10, 2),
            end_date=date(2018, 10, 2),
        )

    def test_date_before_start(self):
        with self.assertRaises(Organisation.DoesNotExist):
            Organisation.objects.all().get_by_date(
                official_identifier='TEST1',
                organisation_type = "local-authority",
                date=date(2015, 12, 1)
            )

    def test_date_after_end(self):
        with self.assertRaises(Organisation.DoesNotExist):
            Organisation.objects.all().get_by_date(
                official_identifier='TEST2',
                organisation_type = "local-authority",
                date=date(2019, 12, 1)
            )

    def test_date_valid_in_range(self):
        o = Organisation.objects.all().get_by_date(
            official_identifier='TEST1',
            organisation_type = "local-authority",
            date=date(2016, 12, 1)
        )
        self.assertEqual('Foo & Bar District Council', o.official_name)

    def test_date_valid_with_null_end(self):
        o = Organisation.objects.all().get_by_date(
            official_identifier='TEST1',
            organisation_type = "local-authority",
            date=date(2018, 12, 1)
        )
        self.assertEqual('Bar with Foo District Council', o.official_name)
