from datetime import date

from django.test import TestCase
from organisations.management.commands.import_divisionsets_from_csv import (
    Command,
)
from organisations.models import Organisation, OrganisationDivisionSet


class ImportDivisionSetsFromCsvTests(TestCase):
    def setUp(self):
        # set up test data

        self.opts = {"url": "foo.bar/baz", "s3": None, "file": None}

        self.org1 = Organisation.objects.create(
            official_identifier="TEST1",
            organisation_type="local-authority",
            official_name="Test Council 1",
            slug="test1",
            territory_code="ENG",
            election_name="Test Council 1 Local Elections",
            start_date=date(2016, 10, 1),
        )
        self.base_record = {
            "Start Date": "",
            "End Date": "",
            "Name": "",
            "official_identifier": "",
            "geography_curie": "",
            "seats_total": "",
            "Boundary Commission Consultation URL": "",
            "Legislation URL": "",
            "Short Title": "",
            "Notes": "",
            "Mapit Generation URI": "",
            "Organisation ID": "",
            "Organisation ID type": "",
            "Territory Code": "ENG",
        }

        self.org3 = Organisation.objects.create(
            official_identifier="TEST3",
            organisation_type="local-authority",
            official_name="Test Council 3",
            slug="test3",
            territory_code="ENG",
            election_name="Test Council 3 Local Elections",
            start_date=date(2016, 10, 1),
        )
        self.org4 = Organisation.objects.create(
            official_identifier="TEST4",
            organisation_type="local-authority",
            official_name="Test Council 4",
            slug="test4",
            territory_code="ENG",
            election_name="Test Council 4 Local Elections",
            start_date=date(2016, 10, 1),
        )
        OrganisationDivisionSet.objects.create(
            organisation=self.org3,
            start_date="2016-10-01",
            end_date="2017-05-03",
            legislation_url="",
            consultation_url="",
            short_title="",
            notes="",
        )
        OrganisationDivisionSet.objects.create(
            organisation=self.org4,
            start_date="2016-10-01",
            end_date="2018-05-02",
            legislation_url="",
            consultation_url="",
            short_title="",
            notes="",
        )

        records = [
            self.base_record.copy(),
            self.base_record.copy(),
            self.base_record.copy(),
            self.base_record.copy(),
        ]
        records[0]["Name"] = "Central"
        records[0]["seats_total"] = "1"
        records[0]["Organisation ID"] = "TEST3"
        records[1]["Name"] = "Abbey"
        records[1]["seats_total"] = "2"
        records[1]["Organisation ID"] = "TEST3"
        records[2]["Name"] = "Castle"
        records[2]["seats_total"] = "3"
        records[2]["Organisation ID"] = "TEST4"
        records[3]["Name"] = "Park"
        records[3]["seats_total"] = "1"
        records[3]["Organisation ID"] = "TEST4"
        self.valid_test_data = records

    def test_org_not_found_bad_code(self):
        # Organisation doesn't exist
        cmd = Command()
        self.base_record[
            "Organisation ID"
        ] = "XXXX"  # this Org ID doesn't exist
        cmd.read_from_url = lambda x: [self.base_record]
        with self.assertRaises(Organisation.DoesNotExist):
            cmd.handle(**self.opts)

    def test_org_not_found_bad_date(self):
        # Organisation code exists, but not valid for this date
        cmd = Command()
        self.base_record["Organisation ID"] = "TEST1"
        self.base_record[
            "Start Date"
        ] = "2016-09-01"  # before TEST1 org start date
        cmd.read_from_url = lambda x: [self.base_record]
        with self.assertRaises(Organisation.DoesNotExist):
            cmd.handle(**self.opts)

    def test_divset_not_found(self):
        # Organisation does exist, but has no associated DivisionSets
        cmd = Command()
        self.base_record["Organisation ID"] = "TEST1"
        cmd.read_from_url = lambda x: [self.base_record]
        with self.assertRaises(Exception):
            cmd.handle(**self.opts)

    def test_divset_null_end_date(self):
        # Organisation does exist and has an associated DivisionSets
        # but the DivisionSet has a NULL end date
        OrganisationDivisionSet.objects.create(
            organisation=self.org1,
            start_date="2016-10-01",
            end_date=None,
            legislation_url="",
            consultation_url="",
            short_title="",
            notes="",
        )
        cmd = Command()
        self.base_record["Organisation ID"] = "TEST1"
        cmd.read_from_url = lambda x: [self.base_record]
        with self.assertRaises(Exception):
            cmd.handle(**self.opts)

    def test_valid(self):
        # all data is valid - should import cleanly
        cmd = Command()
        cmd.read_from_url = lambda x: self.valid_test_data
        cmd.get_division_type_from_registers = lambda x: "DIW"
        cmd.handle(**self.opts)

        # check it all imported correctly
        org3divset = (
            OrganisationDivisionSet.objects.all()
            .filter(organisation=self.org3)
            .order_by("-start_date")
        )
        self.assertEqual(2, len(org3divset))
        self.assertEqual(
            "2017-05-04", org3divset[0].start_date.strftime("%Y-%m-%d")
        )
        self.assertIsNone(org3divset[0].end_date)
        self.assertEqual(2, len(org3divset[0].divisions.all()))

        org4divset = (
            OrganisationDivisionSet.objects.all()
            .filter(organisation=self.org4)
            .order_by("-start_date")
        )
        self.assertEqual(2, len(org4divset))
        self.assertEqual(
            "2018-05-03", org4divset[0].start_date.strftime("%Y-%m-%d")
        )
        self.assertIsNone(org4divset[0].end_date)
        self.assertEqual(2, len(org4divset[0].divisions.all()))
