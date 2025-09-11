import os
import shutil
import tempfile
from unittest import mock

import boto3
from django.core.management import call_command
from django.test import TransactionTestCase, override_settings
from factories import (
    DivisionGeographyFactory,
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
)
from moto import mock_aws
from organisations.models import OrganisationDivisionSet

MOCK_PUBLIC_DATA_BUCKET = "test-pmtiles-store"


@mock_aws
class TestUpdatePmtiles(TransactionTestCase):
    def setUp(self):
        for _ in range(2):
            divisionset = OrganisationDivisionSetFactory()
            for _ in range(5):
                div = OrganisationDivisionFactory(divisionset=divisionset)
                DivisionGeographyFactory(division=div)
            divisionset.save()  # Ensure pmtiles_md5_hash is generated

        # Create a mock S3 bucket
        conn = boto3.resource("s3", region_name="us-east-1")
        conn.create_bucket(Bucket=MOCK_PUBLIC_DATA_BUCKET)

        # Mock STATIC_ROOT with tmp dir
        self.tmp_static_root = tempfile.mkdtemp()
        self.override_static_root = override_settings(
            STATIC_ROOT=self.tmp_static_root
        )
        # Create mock pmtiles-store
        self.static_path = f"{self.tmp_static_root}/pmtiles-store"
        os.makedirs(self.static_path)

        self.override_static_root.enable()

    def tearDown(self):
        # Reset Mock STATIC_ROOT
        self.override_static_root.disable()
        shutil.rmtree(self.tmp_static_root)

    def test_create_pmtiles_when_file_absent(self):
        call_command("update_pmtiles")
        divsets = OrganisationDivisionSet.objects.all()
        has_files = [ds.has_pmtiles_file for ds in divsets]
        assert all(has_files)

    def test_create_pmtiles_and_update_hash_when_hash_absent(self):
        # Create a new divisionset without a hash
        divisionset = OrganisationDivisionSetFactory()
        for _ in range(5):
            div = OrganisationDivisionFactory(divisionset=divisionset)
            DivisionGeographyFactory(division=div)

        call_command("update_pmtiles")

        divsets = OrganisationDivisionSet.objects.all()

        hashes = [ds.pmtiles_md5_hash for ds in divsets]
        has_files = [ds.has_pmtiles_file for ds in divsets]
        assert all(has_files)
        assert all(hashes)

    def test_skips_divset_when_file_hash_matches(self):
        divset = OrganisationDivisionSet.objects.first()
        fake_fp = f"{self.static_path}/{divset.pmtiles_file_name}"
        with open(fake_fp, "w") as f:
            f.write("dummy data")

        with mock.patch(
            "organisations.management.commands.update_pmtiles.call_command"
        ) as create_pmtiles_call:
            call_command("update_pmtiles")

            create_pmtiles_call.assert_called_once()
