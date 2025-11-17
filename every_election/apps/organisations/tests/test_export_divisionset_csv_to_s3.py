import boto3
from django.core.management import CommandError, call_command
from django.test import TestCase
from moto import mock_aws
from organisations.tests.factories import (
    DivisionGeographyFactory,
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
)

MOCK_DATA_CACHE = "ee.data-cache.local"


@mock_aws
class TestExportDivisionSetCSVToS3(TestCase):
    def setUp(self):
        super().setUp()
        # Create a mock S3 bucket
        self.s3 = boto3.resource("s3", region_name="us-east-1")
        self.s3.create_bucket(Bucket=MOCK_DATA_CACHE)

        self.divisionset = OrganisationDivisionSetFactory()
        for i in range(2):
            div = OrganisationDivisionFactory(divisionset=self.divisionset)
            DivisionGeographyFactory(division=div)

    def test_divisionset_does_not_exist(self):
        with self.assertRaises(CommandError):
            call_command("export_divisionset_csv_to_s3", 9999)

    def test_divisionset_has_no_divisiong_geographies(self):
        self.divisionset.divisions.all().delete()
        with self.assertRaises(CommandError):
            call_command("export_divisionset_csv_to_s3", self.divisionset.id)

    def test_export_divisionset_csv_to_s3(self):
        s3_key = f"divisionsets-with-wkt/{self.divisionset.id}.csv"

        call_command(
            "export_divisionset_csv_to_s3",
            self.divisionset.id,
            bucket=MOCK_DATA_CACHE,
        )

        bucket = self.s3.Bucket(MOCK_DATA_CACHE)
        objs = list(bucket.objects.filter(Prefix=s3_key))
        self.assertEqual(len(objs), 1)
