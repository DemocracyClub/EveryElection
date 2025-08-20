import os
import shutil
import tempfile

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from factories import (
    OrganisationDivisionSetFactory,
)

PUBLIC_DATA_BUCKET = "test-pmtiles-store"


class TestPMTilesView(TestCase):
    def setUp(self):
        self.divisionset = OrganisationDivisionSetFactory()
        # Mock STATIC_ROOT with tmp dir
        self.tmp_static_root = tempfile.mkdtemp()
        self.override_static_root = override_settings(
            STATIC_ROOT=self.tmp_static_root
        )
        self.override_static_root.enable()
        # Create dummy pmtiles file
        static_path = f"{settings.STATIC_ROOT}/pmtiles-store"
        self.pmtiles_fp = f"{static_path}/{self.divisionset.pmtiles_file_name}"
        os.makedirs(static_path, exist_ok=True)
        with open(self.pmtiles_fp, "w") as f:
            f.write("dummy data")

    def tearDown(self):
        self.override_static_root.disable()
        shutil.rmtree(self.tmp_static_root)

    def test_pmtiles_file_not_found(self):
        # Remove the dummy file to simulate not found
        os.remove(self.pmtiles_fp)

        test_url = reverse("pmtiles_view", args=[self.divisionset.id])
        resp = self.client.get(test_url)
        self.assertEqual(resp.status_code, 404)

    def test_serve_pmtiles_file(self):
        test_url = reverse("pmtiles_view", args=[self.divisionset.id])
        resp = self.client.get(test_url)
        self.assertEqual(resp.status_code, 200)

    def test_accepts_range_requests(self):
        test_url = reverse("pmtiles_view", args=[self.divisionset.id])
        resp = self.client.get(test_url, HTTP_RANGE="bytes=0-9")
        self.assertEqual(resp.status_code, 206)
        self.assertEqual(resp["Content-Length"], "10")
        self.assertEqual(resp["Content-Range"], "bytes 0-9/10")
