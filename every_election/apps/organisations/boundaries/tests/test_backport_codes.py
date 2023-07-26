import os
from datetime import date
from io import StringIO
from django.test import TestCase
from organisations.boundaries.management.commands.boundaryline_backport_codes import (
    Command,
)
from organisations.models import OrganisationDivision


def count_divs_by_prefix(prefix):
    return (
        OrganisationDivision.objects.all()
        .filter(official_identifier__startswith=prefix)
        .count()
    )


class BackportCodesTests(TestCase):
    fixtures = ["croydon-metadata-tempcodes.json", "croydon-geographies.json"]

    def setUp(self):
        super().setUp()

        self.opts = {
            "url": None,
            "s3": None,
            "file": os.path.abspath(
                "every_election/apps/organisations/boundaries/fixtures/boundaryline_subset"
            ),
            "dry-run": None,
            "verbosity": 1,
            "date": date(2018, 5, 4),
        }

        # sanity checks on init state
        # should start off with 28 divisions with a temp identifier
        self.assertEqual(28, count_divs_by_prefix("CRY:"))
        # ..and 24 with a GSS code
        self.assertEqual(24, count_divs_by_prefix("gss:"))

    def run_command_with_test_data(self):
        cmd = Command()
        # override WARD_TYPES for convenience
        # just so that we don't have to provide a test version of
        # unitary_electoral_division_region.shp as well
        cmd.WARD_TYPES = "LBW"
        cmd.stdout = StringIO()
        cmd.handle(**self.opts)
        cmd.stdout.seek(0)
        output = cmd.stdout.read()
        return output

    def test_write(self):
        output = self.run_command_with_test_data()

        # now we should only have one left with a temp identifier
        # (1 should be 'not found' in BoundaryLine)
        self.assertEqual(1, count_divs_by_prefix("CRY:"))
        # ..and 51 with a GSS code
        self.assertEqual(51, count_divs_by_prefix("gss:"))

        self.assertIn("Searched 28 divisions", output)
        self.assertIn("Found 27 codes", output)
        self.assertIn(
            "Could not find a code for division CRY:shirley-south", output
        )

    def test_dry_run(self):
        self.opts["dry-run"] = True
        output = self.run_command_with_test_data()

        # database content should not have changed
        self.assertEqual(28, count_divs_by_prefix("CRY:"))
        self.assertEqual(24, count_divs_by_prefix("gss:"))

        # but we should still output info on the console
        self.assertIn("Searched 28 divisions", output)
        self.assertIn("Found 27 codes", output)
        self.assertIn(
            "Could not find a code for division CRY:shirley-south", output
        )

    def test_no_divisions_found(self):
        self.opts["date"] = date(2001, 1, 1)
        output = self.run_command_with_test_data()

        # database content should not have changed
        self.assertEqual(28, count_divs_by_prefix("CRY:"))
        self.assertEqual(24, count_divs_by_prefix("gss:"))

        self.assertIn("Searched 0 divisions", output)
