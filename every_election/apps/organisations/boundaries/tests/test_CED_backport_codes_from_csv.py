import json
import os
import tempfile
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from organisations.models import (
    OrganisationDivision,
    OrganisationDivisionSet,
)
from organisations.tests.factories import (
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
    OrganisationFactory,
)


def count_divs_by_prefix(prefix):
    return (
        OrganisationDivision.objects.all()
        .filter(official_identifier__startswith=prefix)
        .count()
    )


class CEDBackportGSSCodesTests(TestCase):
    def setUp(self):
        super().setUp()

        self.opts = {
            "file": os.path.abspath(
                "every_election/apps/organisations/boundaries/fixtures/ward_to_ced_county_sample.csv"
            ),
        }

        organisation = OrganisationFactory(slug="cambridgeshire")
        division_set = OrganisationDivisionSetFactory(organisation=organisation)

        sample_divisions = [
            "abbey",
            "alconbury-kimbolton",
            "arbury",
            "bar-hill",
        ]

        for slug in sample_divisions:
            OrganisationDivisionFactory(
                divisionset=division_set,
                division_type="CED",
                official_identifier="CAM:" + slug,
                slug=slug,
            )

    def run_command_with_test_data(self):
        out = StringIO()
        call_command("CED_backport_GSS_codes_from_csv", **self.opts, stdout=out)
        return out.getvalue()

    def test_backport_single_divset(self):
        self.opts["divset-id"] = OrganisationDivisionSet.objects.first().id

        output = self.run_command_with_test_data()
        # 1 should not be found in the sample CSV
        self.assertEqual(1, count_divs_by_prefix("CAM:"))
        # ..and 3 should now have a GSS code
        self.assertEqual(3, count_divs_by_prefix("gss:"))

        self.assertIn("Searched 4 divisions", output)
        self.assertIn("Matched 3 codes", output)
        self.assertIn("Could not find a code for division", output)

    def test_backport_multiple_divsets(self):
        # Create 2nd divset for a different organisation
        ham_divset = OrganisationDivisionSetFactory(
            organisation=OrganisationFactory(slug="hampshire")
        )
        sample_divisions = ["baddesley", "andover-north"]

        for slug in sample_divisions:
            OrganisationDivisionFactory(
                divisionset=ham_divset,
                division_type="CED",
                official_identifier="HAM:" + slug,
                slug=slug,
            )
        # Create a temp json file with divset ids
        divset_ids = list(
            OrganisationDivisionSet.objects.values_list("id", flat=True)
        )
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            tmp.write(json.dumps(divset_ids).encode())
            tmp.seek(0)
            self.opts["divset-ids"] = tmp.name
            output = self.run_command_with_test_data()

        # 1 should not be found in the sample CSV
        self.assertEqual(
            1, count_divs_by_prefix("HAM:") + count_divs_by_prefix("CAM:")
        )
        # ..and 5 should now have a GSS code
        self.assertEqual(5, count_divs_by_prefix("gss:"))

        self.assertIn("Searched 6 divisions", output)
        self.assertIn("Matched 5 codes", output)
        self.assertIn("Could not find a code for division", output)

    def test_dry_run(self):
        self.opts["dry-run"] = True
        self.opts["divset-id"] = OrganisationDivisionSet.objects.first().id

        output = self.run_command_with_test_data()

        # database content should not have changed
        self.assertEqual(4, count_divs_by_prefix("CAM:"))
        self.assertEqual(0, count_divs_by_prefix("gss:"))

        # but we should still output info on the console
        self.assertIn("Searched 4 divisions", output)
        self.assertIn("Matched 3 codes", output)
        self.assertIn("Could not find a code for division", output)
