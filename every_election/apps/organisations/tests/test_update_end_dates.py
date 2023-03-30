from datetime import date
from io import StringIO
import os
from django.test import TestCase
from organisations.models import Organisation, OrganisationDivisionSet
from organisations.management.commands.update_end_dates import Command


class UpdateEndDatesTests(TestCase):
    def setUp(self):
        # set up test data
        self.org1 = Organisation.objects.create(
            official_identifier="TEST1",
            organisation_type="local-authority",
            official_name="Test Council 1",
            slug="test1",
            territory_code="ENG",
            election_name="Test Council 1 Local Elections",
            start_date=date(2004, 12, 2),
        )
        self.org2 = Organisation.objects.create(
            official_identifier="TEST2",
            organisation_type="local-authority",
            official_name="Test Council 2",
            slug="test2",
            territory_code="ENG",
            election_name="Test Council 2 Local Elections",
            start_date=date(2004, 12, 2),
        )
        self.org3 = Organisation.objects.create(
            official_identifier="TEST3",
            organisation_type="local-authority",
            official_name="Test Council 3",
            slug="test3",
            territory_code="ENG",
            election_name="Test Council 3 Local Elections",
            start_date=date(2004, 12, 2),
            end_date=date(2020, 4, 4),
        )
        OrganisationDivisionSet.objects.create(
            organisation=self.org1,
            start_date="2004-12-02",
            end_date=None,
            legislation_url="",
            consultation_url="",
            short_title="",
            notes="",
        )
        OrganisationDivisionSet.objects.create(
            organisation=self.org2,
            start_date="2004-12-02",
            end_date=None,
            legislation_url="",
            consultation_url="",
            short_title="",
            notes="",
        )
        OrganisationDivisionSet.objects.create(
            organisation=self.org3,
            start_date="2004-12-02",
            end_date="2007-01-14",
            legislation_url="",
            consultation_url="",
            short_title="",
            notes="",
        )

    def assertNoChanges(self):
        ods1 = OrganisationDivisionSet.objects.get(
            organisation=self.org1, start_date="2004-12-02"
        )
        ods2 = OrganisationDivisionSet.objects.get(
            organisation=self.org2, start_date="2004-12-02"
        )
        ods3 = OrganisationDivisionSet.objects.get(
            organisation=self.org3, start_date="2004-12-02"
        )
        self.assertEqual(None, ods1.end_date)
        self.assertEqual(None, ods2.end_date)
        self.assertEqual("2007-01-14", ods3.end_date.strftime("%Y-%m-%d"))

    def test_valid(self):
        dirname = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.abspath(os.path.join(dirname, "test_data/valid.csv"))
        cmd = Command()

        # supress output
        out = StringIO()
        cmd.stdout = out

        cmd.handle(**{"file": filename, "url": None, "s3": None, "overwrite": False})
        ods1 = OrganisationDivisionSet.objects.get(
            organisation=self.org1, start_date="2004-12-02"
        )
        ods2 = OrganisationDivisionSet.objects.get(
            organisation=self.org2, start_date="2004-12-02"
        )
        ods3 = OrganisationDivisionSet.objects.get(
            organisation=self.org3, start_date="2004-12-02"
        )
        self.assertEqual("2018-04-02", ods1.end_date.strftime("%Y-%m-%d"))
        self.assertEqual("2017-12-31", ods2.end_date.strftime("%Y-%m-%d"))
        self.assertEqual("2007-01-14", ods3.end_date.strftime("%Y-%m-%d"))

    def test_unexpected_headers(self):
        dirname = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.abspath(
            os.path.join(dirname, "test_data/unexpected_headers.csv")
        )
        cmd = Command()

        # supress output
        out = StringIO()
        cmd.stdout = out

        with self.assertRaises(ValueError):
            cmd.handle(
                **{"file": filename, "url": None, "s3": None, "overwrite": False}
            )

        # no end dates should have changed
        self.assertNoChanges()

    def test_org_not_in_db(self):
        dirname = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.abspath(os.path.join(dirname, "test_data/org_not_in_db.csv"))
        cmd = Command()

        # supress output
        out = StringIO()
        cmd.stdout = out

        with self.assertRaises(Organisation.DoesNotExist):
            cmd.handle(
                **{"file": filename, "url": None, "s3": None, "overwrite": False}
            )

        # no end dates should have changed
        self.assertNoChanges()

    def test_bad_date_format(self):
        dirname = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.abspath(
            os.path.join(dirname, "test_data/bad_date_format.csv")
        )
        cmd = Command()

        # supress output
        out = StringIO()
        cmd.stdout = out

        with self.assertRaises(ValueError):
            cmd.handle(
                **{"file": filename, "url": None, "s3": None, "overwrite": False}
            )

        # no end dates should have changed
        self.assertNoChanges()

    def test_invalid_division_set(self):
        # org is valid but divset start_date not found
        dirname = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.abspath(
            os.path.join(dirname, "test_data/invalid_division_set.csv")
        )
        cmd = Command()

        # supress output
        out = StringIO()
        cmd.stdout = out

        with self.assertRaises(OrganisationDivisionSet.DoesNotExist):
            cmd.handle(
                **{"file": filename, "url": None, "s3": None, "overwrite": False}
            )

        # no end dates should have changed
        self.assertNoChanges()

    def test_overwrite_param(self):
        # set end dates so it is not null
        ods = OrganisationDivisionSet.objects.get(
            organisation=self.org1, start_date="2004-12-02"
        )
        ods.end_date = "2020-01-01"
        ods.save()

        dirname = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.abspath(os.path.join(dirname, "test_data/valid.csv"))
        cmd = Command()

        # supress output
        out = StringIO()
        cmd.stdout = out

        # run updates with overwrite=False
        cmd.handle(**{"file": filename, "url": None, "s3": None, "overwrite": False})

        # end date shouldn't have changed
        ods = OrganisationDivisionSet.objects.get(
            organisation=self.org1, start_date="2004-12-02"
        )
        self.assertEqual("2020-01-01", ods.end_date.strftime("%Y-%m-%d"))

        # now run it again with overwrite=True
        cmd.handle(**{"file": filename, "url": None, "s3": None, "overwrite": True})

        # this time it should have been ovewrwritten with the new value
        ods = OrganisationDivisionSet.objects.get(
            organisation=self.org1, start_date="2004-12-02"
        )
        self.assertEqual("2018-04-02", ods.end_date.strftime("%Y-%m-%d"))

    def test_invalid_start_date(self):
        # org code is valid but divset start_date before org start_date
        dirname = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.abspath(
            os.path.join(dirname, "test_data/invalid_start_date.csv")
        )
        cmd = Command()

        # supress output
        out = StringIO()
        cmd.stdout = out

        with self.assertRaises(Organisation.DoesNotExist):
            cmd.handle(
                **{"file": filename, "url": None, "s3": None, "overwrite": False}
            )

        # no end dates should have changed
        self.assertNoChanges()

    def test_invalid_end_date(self):
        # org is valid but divset end_date after org end_date
        dirname = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.abspath(
            os.path.join(dirname, "test_data/invalid_end_date.csv")
        )
        cmd = Command()

        # supress output
        out = StringIO()
        cmd.stdout = out

        with self.assertRaises(ValueError):
            cmd.handle(
                **{"file": filename, "url": None, "s3": None, "overwrite": False}
            )

        # no end dates should have changed
        self.assertNoChanges()
