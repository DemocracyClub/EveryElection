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

    def tearDown(self):
        self.override_static_root.disable()
        shutil.rmtree(self.tmp_static_root)

    def test_pmtiles_file_not_found_locally(self):
        test_url = reverse("pmtiles_view", args=[self.divisionset.id])
        resp = self.client.get(test_url)
        self.assertEqual(resp.status_code, 404)

    def test_serve_pmtiles_file_locally(self):
        static_path = f"{settings.STATIC_ROOT}/pmtiles-store"
        pmtiles_fp = f"{static_path}/{self.divisionset.pmtiles_file_name}"
        os.makedirs(static_path, exist_ok=True)
        with open(pmtiles_fp, "w") as f:
            f.write("dummy data")

        test_url = reverse("pmtiles_view", args=[self.divisionset.id])
        resp = self.client.get(test_url)
        self.assertEqual(resp.status_code, 200)

    @override_settings(PUBLIC_DATA_BUCKET=PUBLIC_DATA_BUCKET)
    def test_redirect_to_s3(self):
        test_url = reverse("pmtiles_view", args=[self.divisionset.id])
        resp = self.client.get(test_url)
        redirect_url = f"https://s3.eu-west-2.amazonaws.com/{PUBLIC_DATA_BUCKET}/{self.divisionset.pmtiles_s3_key}"
        self.assertRedirects(
            resp, redirect_url, status_code=302, fetch_redirect_response=False
        )
