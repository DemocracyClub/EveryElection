import os
import shutil
import tempfile
from io import StringIO
from unittest import mock

import boto3
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from factories import (
    DivisionGeographyFactory,
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
)
from moto import mock_aws
from organisations.models import OrganisationDivisionSet

MOCK_PUBLIC_DATA_BUCKET = "test-pmtiles-store"


def mock_create_pmtile(self, temp_dir):
    filepath = os.path.join(temp_dir, self.divset.pmtiles_file_name)
    with open(filepath, "w") as f:
        f.write("dummy pmtiles content")
    return filepath


@mock_aws
class TestUpdatePmtiles(TestCase):
    def setUp(self):
        # Patch create_pmtile to avoid actually running tippecanoe
        self.mock_create_pmtile_patcher = mock.patch(
            "organisations.pmtiles_creator.PMtilesCreator.create_pmtile",
            side_effect=mock_create_pmtile,
            autospec=True,
        )

        self.send_event_patcher = mock.patch(
            "organisations.management.commands.update_pmtiles.send_event",
            autospec=True,
        )

        self.mock_create_pmtile = self.mock_create_pmtile_patcher.start()
        self.mock_send_event = self.send_event_patcher.start()

        for _ in range(2):
            divisionset = OrganisationDivisionSetFactory()
            for _ in range(5):
                div = OrganisationDivisionFactory(divisionset=divisionset)
                DivisionGeographyFactory(division=div)
            divisionset.save()  # Ensure pmtiles_md5_hash is generated

        # Create a mock S3 bucket
        self.s3 = boto3.resource("s3", region_name="us-east-1")
        self.s3.create_bucket(Bucket=MOCK_PUBLIC_DATA_BUCKET)

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
        self.mock_create_pmtile_patcher.stop()
        self.send_event_patcher.stop()
        # Reset Mock STATIC_ROOT
        self.override_static_root.disable()
        shutil.rmtree(self.tmp_static_root)

    def test_create_pmtiles_when_file_absent(self):
        call_command("update_pmtiles", all=True)
        divsets = OrganisationDivisionSet.objects.all()
        has_files = [ds.has_pmtiles_file for ds in divsets]
        assert all(has_files)

    def test_send_event_called_once_on_file_creation(self):
        # test setup creates multiple divisionsets without pmtiles files
        call_command("update_pmtiles", all=True)
        # we only want to send one event for the whole run
        self.mock_send_event.assert_called_once()

    @override_settings(PUBLIC_DATA_BUCKET=MOCK_PUBLIC_DATA_BUCKET)
    def test_create_pmtiles_when_file_absent_s3(self):
        call_command("update_pmtiles", all=True)
        divsets = OrganisationDivisionSet.objects.all()
        has_files = [ds.has_pmtiles_file for ds in divsets]
        assert all(has_files)

    def test_create_pmtiles_and_update_hash_when_hash_absent(self):
        # Create a new divisionset without a hash
        divisionset = OrganisationDivisionSetFactory()
        for _ in range(5):
            div = OrganisationDivisionFactory(divisionset=divisionset)
            DivisionGeographyFactory(division=div)

        call_command("update_pmtiles", all=True)

        divsets = OrganisationDivisionSet.objects.all()

        hashes = [ds.pmtiles_md5_hash for ds in divsets]
        has_files = [ds.has_pmtiles_file for ds in divsets]
        assert all(has_files)
        assert all(hashes)

    @override_settings(PUBLIC_DATA_BUCKET=MOCK_PUBLIC_DATA_BUCKET)
    def test_create_pmtiles_and_update_hash_when_hash_absent_s3(self):
        # Create a new divisionset without a hash
        divisionset = OrganisationDivisionSetFactory()
        for _ in range(5):
            div = OrganisationDivisionFactory(divisionset=divisionset)
            DivisionGeographyFactory(division=div)

        call_command("update_pmtiles", all=True)

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

        call_command("update_pmtiles", all=True)

        self.mock_create_pmtile.assert_called_once()

    @override_settings(PUBLIC_DATA_BUCKET=MOCK_PUBLIC_DATA_BUCKET)
    def test_skips_divset_when_file_hash_matches_s3(self):
        divset = OrganisationDivisionSet.objects.first()

        bucket = self.s3.Bucket(MOCK_PUBLIC_DATA_BUCKET)
        fake_file = bucket.Object(
            MOCK_PUBLIC_DATA_BUCKET, key=divset.pmtiles_s3_key
        )
        fake_file.put(Body="dummy data")

        call_command("update_pmtiles", all=True)

        self.mock_create_pmtile.assert_called_once()

    def test_update_hash_and_overwrite_pmtiles_when_file_hash_mismatch(self):
        # create the pmtiles
        call_command("update_pmtiles", all=True)
        divset = OrganisationDivisionSet.objects.first()
        original_hash = divset.pmtiles_md5_hash
        original_files = os.listdir(self.static_path)
        # invalidate hash
        div = divset.divisions.first()
        div.name = "new name"
        div.save()

        call_command("update_pmtiles", all=True)

        new_files = os.listdir(self.static_path)
        divset.refresh_from_db()
        new_hash = divset.pmtiles_md5_hash
        assert original_hash != new_hash
        # assert old file was removed
        assert len(original_files) == len(new_files)
        # assert files are different
        assert sorted(original_files) != sorted(new_files)

    @override_settings(PUBLIC_DATA_BUCKET=MOCK_PUBLIC_DATA_BUCKET)
    def test_update_hash_and_overwrite_pmtiles_when_file_hash_mismatch_s3(self):
        # create the pmtiles
        call_command("update_pmtiles", all=True)
        divset = OrganisationDivisionSet.objects.first()
        bucket = self.s3.Bucket(MOCK_PUBLIC_DATA_BUCKET)
        original_hash = divset.pmtiles_md5_hash
        original_files = [obj.key for obj in bucket.objects.all()]
        # invalidate hash
        div = divset.divisions.first()
        div.name = "new name"
        div.save()

        call_command("update_pmtiles", all=True)

        new_files = [obj.key for obj in bucket.objects.all()]
        divset.refresh_from_db()
        new_hash = divset.pmtiles_md5_hash
        assert original_hash != new_hash
        # assert old file was removed
        assert len(original_files) == len(new_files)
        # assert files are different
        assert sorted(original_files) != sorted(new_files)

    def test_overwrite_argument(self):
        stdout = StringIO()
        call_command("update_pmtiles", all=True)
        call_command("update_pmtiles", all=True, stdout=stdout)

        assert self.mock_create_pmtile.call_count == 2
        self.assertIn("skipping", stdout.getvalue().lower())

        call_command("update_pmtiles", all=True, overwrite=True)
        assert self.mock_create_pmtile.call_count == 4

    def test_divset_ids_argument(self):
        divset = OrganisationDivisionSet.objects.first()
        assert divset.has_pmtiles_file is False
        call_command("update_pmtiles", divset_ids=[divset.id])
        # Get divset from database again to invalidate cached has_pmtiles_file property
        divset = OrganisationDivisionSet.objects.get(id=divset.id)
        assert divset.has_pmtiles_file is True

    @override_settings(PUBLIC_DATA_BUCKET=MOCK_PUBLIC_DATA_BUCKET)
    def test_divset_ids_argument_s3(self):
        divset = OrganisationDivisionSet.objects.first()
        assert divset.has_pmtiles_file is False
        call_command("update_pmtiles", divset_ids=[divset.id])
        # Get divset from database again to invalidate cached has_pmtiles_file property
        divset = OrganisationDivisionSet.objects.get(id=divset.id)
        assert divset.has_pmtiles_file is True

    def test_divset_has_no_division_geographies(self):
        divset = OrganisationDivisionSet.objects.first()
        divset.get_division_geographies().delete()
        with self.assertRaises(CommandError):
            stdout = StringIO()
            call_command(
                "update_pmtiles", divset_ids=[divset.id], stdout=stdout
            )
            self.assertIn(
                "has no division geographies", stdout.getvalue().lower()
            )
            self.assertFalse(divset.has_pmtiles_file)

    def test_divset_does_not_exist(self):
        with self.assertRaises(CommandError):
            stdout = StringIO()
            call_command("update_pmtiles", divset_ids=[1000], stdout=stdout)
            self.assertIn("do not exist", stdout.getvalue().lower())

    def test_pmtiles_creation_fails(self):
        error = "Tippecanoe failed"
        self.mock_create_pmtile.side_effect = Exception(error)
        with self.assertRaises(CommandError):
            stdout = StringIO()
            call_command("update_pmtiles", all=True, stdout=stdout)
            self.assertIn(error, stdout.getvalue())

    def test_invalid_hash_no_existing_files(self):
        divset = OrganisationDivisionSet.objects.first()
        original_hash = divset.pmtiles_md5_hash
        # invalidate hash
        div = divset.divisions.first()
        div.name = "new name"
        div.save()

        call_command("update_pmtiles", all=True)

        divset.refresh_from_db()
        new_hash = divset.pmtiles_md5_hash
        # assert hash was updated
        assert original_hash != new_hash
