import os
import shutil
import tempfile
from io import StringIO

import boto3
from django.conf import settings
from django.core.management import CommandError, call_command
from django.test import TransactionTestCase, override_settings
from factories import (
    DivisionGeographyFactory,
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
)
from moto import mock_aws

PUBLIC_DATA_BUCKET = "test-pmtiles-store"


class TestCreatePMtilesForDivSet(TransactionTestCase):
    def setUp(self):
        self.divisionset = OrganisationDivisionSetFactory()
        for _ in range(5):
            div = OrganisationDivisionFactory(divisionset=self.divisionset)
            DivisionGeographyFactory(division=div)
        # Mock STATIC_ROOT with tmp dir
        self.tmp_static_root = tempfile.mkdtemp()
        self.override_static_root = override_settings(
            STATIC_ROOT=self.tmp_static_root
        )
        self.override_static_root.enable()

    def tearDown(self):
        self.override_static_root.disable()
        shutil.rmtree(self.tmp_static_root)

    def test_create_pmtiles_for_divset_locally(self):
        divset_id = self.divisionset.id
        static_path = f"{settings.STATIC_ROOT}/pmtiles-store"
        pmtiles_fp = f"{static_path}/{self.divisionset.pmtiles_file_name}"
        # Ensure the PMTile file does not exist before running the command
        self.assertFalse(os.path.exists(pmtiles_fp))
        # Call the management command
        call_command("create_pmtiles_for_divset", divset_id)
        # Check if the pmtiles file was created
        self.assertTrue(os.path.exists(pmtiles_fp))

    def test_pmtiles_already_exists_locally(self):
        divset_id = self.divisionset.id
        static_path = f"{settings.STATIC_ROOT}/pmtiles-store"
        pmtiles_fp = f"{static_path}/{self.divisionset.pmtiles_file_name}"

        os.makedirs(static_path, exist_ok=True)
        with open(pmtiles_fp, "w") as f:
            f.write("dummy data")

        stdout = StringIO()
        call_command("create_pmtiles_for_divset", divset_id, stdout=stdout)
        self.assertIn("already exists", stdout.getvalue().lower())

    @mock_aws
    @override_settings(PUBLIC_DATA_BUCKET=PUBLIC_DATA_BUCKET)
    def test_create_pmtiles_for_divset_on_s3(self):
        conn = boto3.resource("s3", region_name="us-east-1")
        conn.create_bucket(Bucket=PUBLIC_DATA_BUCKET)

        divset_id = self.divisionset.id
        # Call the management command
        call_command("create_pmtiles_for_divset", divset_id)
        # Check if the pmtiles file was created
        pmtiles_file = conn.Object(
            PUBLIC_DATA_BUCKET, self.divisionset.pmtiles_s3_key
        )

        pmtiles_file.load()  # Should raise an error if the file does not exist
        self.assertEqual(pmtiles_file.bucket_name, PUBLIC_DATA_BUCKET)

    @mock_aws
    @override_settings(PUBLIC_DATA_BUCKET=PUBLIC_DATA_BUCKET)
    def test_pmtiles_already_exists_on_s3(self):
        divset_id = self.divisionset.id
        conn = boto3.resource("s3", region_name="us-east-1")
        conn.create_bucket(Bucket=PUBLIC_DATA_BUCKET)
        pmtiles_file = conn.Object(
            PUBLIC_DATA_BUCKET, self.divisionset.pmtiles_s3_key
        )
        pmtiles_file.put(Body="dummy data")

        stdout = StringIO()
        call_command("create_pmtiles_for_divset", divset_id, stdout=stdout)
        self.assertIn("already exists", stdout.getvalue().lower())

    def test_divset_not_found(self):
        with self.assertRaises(CommandError):
            # Use a non-existent id
            call_command("create_pmtiles_for_divset", 1000)

    def test_divset_has_no_divisions(self):
        self.divisionset.divisions.all().delete()
        with self.assertRaises(CommandError):
            call_command("create_pmtiles_for_divset", self.divisionset.id)
