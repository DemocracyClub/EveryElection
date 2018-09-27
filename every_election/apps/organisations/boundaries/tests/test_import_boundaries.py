import os
import tempfile
from io import StringIO
from django.contrib.gis.geos import MultiPolygon
from django.test import TestCase
from organisations.boundaries.management.commands.boundaryline_import_boundaries import Command
from organisations.models import (
    DivisionGeography,
    OrganisationGeography,
    OrganisationDivision
)


def count_divs_by_source(source):
    return DivisionGeography.objects.all().filter(source=source).count()


class ImportBoundariesTests(TestCase):

    fixtures = [
        'croydon-metadata-gsscodes.json',
        'croydon-geographies.json',
        'tintagel-metadata.json',
    ]

    def setUp(self):
        super().setUp()

        self.opts = {
            'url': None,
            's3': None,
            'file': os.path.abspath(
                'every_election/apps/organisations/boundaries/fixtures/boundaryline_subset'
            ),
            'verbosity': 1,
            'source': 'imported in unit test',
            'all': False,
            'code': None,
        }

        # sanity checks on init state
        # should start off with 28 boundaries from LGBCE
        self.assertEqual(28, count_divs_by_source('lgbce'))
        # ..and 24 from some unknown source
        self.assertEqual(24, count_divs_by_source('unknown'))

        self.assertEqual(0, count_divs_by_source('imported in unit test'))

    def run_command_with_test_data(self):
        cmd = Command()
        cmd.stdout = StringIO()
        cmd.handle(**self.opts)
        cmd.stdout.seek(0)
        output = cmd.stdout.read()
        return output

    def test_import_division_not_found(self):
        # gss:X01000001 is not a valid division in our DB fixture
        self.opts['code'] = 'gss:X01000001'
        output = self.run_command_with_test_data()

        self.assertIn('FAILED', output)
        self.assertIn('X01000001: OrganisationDivision matching query does not exist', output)

        # DB content should not have changed
        self.assertEqual(28, count_divs_by_source('lgbce'))
        self.assertEqual(24, count_divs_by_source('unknown'))
        self.assertEqual(0, count_divs_by_source('imported in unit test'))

    def test_import_boundary_not_found(self):
        # gss:E05000148 is a valid division in our DB fixture
        # but it doesn't exist in our BoundaryLine fixture
        self.opts['code'] = 'gss:E05000148'
        output = self.run_command_with_test_data()

        self.assertIn('FAILED', output)
        self.assertIn('Expected one match for E05000148, found 0', output)

        # DB content should not have changed
        self.assertEqual(28, count_divs_by_source('lgbce'))
        self.assertEqual(24, count_divs_by_source('unknown'))
        self.assertEqual(0, count_divs_by_source('imported in unit test'))

    def test_import_single_boundary_overwrite(self):
        # gss:E05011464 already has a geography
        self.assertEqual('lgbce',
            OrganisationDivision.objects.all().get(
                official_identifier='gss:E05011464'
            ).geography.source
        )

        # but we're going to overwrite it with a new one from BoundaryLine
        self.opts['code'] = 'gss:E05011464'
        output = self.run_command_with_test_data()

        self.assertIn('0 Failures', output)
        self.assertEqual(27, count_divs_by_source('lgbce'))
        self.assertEqual('imported in unit test',
            OrganisationDivision.objects.all().get(
                official_identifier='gss:E05011464'
            ).geography.source
        )

    def test_import_single_boundary_create(self):
        # this time we'll delete the geography record
        # for gss:E05011464 before we start
        OrganisationDivision.objects.all().get(
            official_identifier='gss:E05011464'
        ).geography.delete()

        # importing from BoundaryLine should create a new record
        self.opts['code'] = 'gss:E05011464'
        output = self.run_command_with_test_data()

        self.assertIn('0 Failures', output)
        self.assertEqual(27, count_divs_by_source('lgbce'))
        self.assertEqual('imported in unit test',
            OrganisationDivision.objects.all().get(
                official_identifier='gss:E05011464'
            ).geography.source
        )

    def test_import_boundary_with_detached_parts(self):
        self.opts['code'] = 'gss:E05009271'
        output = self.run_command_with_test_data()

        self.assertIn('0 Failures', output)
        imported_geo = OrganisationDivision.objects.all().get(
            official_identifier='gss:E05009271'
        ).geography.geography

        # In our input fixture, E05009271 matches 2 records:
        # one is a MultiPolygon with 3 polygons in it
        # the other is a single polygon object

        # Importing this should have consolidated that into
        # a single MultiPolygon object with 4 polygons in it
        self.assertIsInstance(imported_geo, MultiPolygon)
        self.assertEqual(4, len(imported_geo))

    def test_import_multiple_boundaries(self):
        # import 3 boundaries by passing a list of 3 codes
        # as a json file containing an array array
        tmp = tempfile.NamedTemporaryFile(suffix='.json')
        tmp.write(b'''[
            "gss:E05011462",
            "gss:E05011463",
            "gss:E05011464"
        ]''')
        tmp.seek(0)
        self.opts['codes'] = tmp.name
        output = self.run_command_with_test_data()
        tmp.close()

        self.assertIn('Imported 3 boundaries', output)
        self.assertIn('0 Failures', output)
        self.assertEqual(25, count_divs_by_source('lgbce'))
        self.assertEqual(3, count_divs_by_source('imported in unit test'))

    def test_import_invalid_ids(self):
        # should throw errors on various spurious/invalidinputs

        self.opts['code'] = 'cheese'
        with self.assertRaises(ValueError):
            self.run_command_with_test_data()

        self.opts['code'] = 'gss:cheese'
        with self.assertRaises(ValueError):
            self.run_command_with_test_data()

        self.opts['code'] = 'unit_id:12345'
        with self.assertRaises(ValueError):
            self.run_command_with_test_data()

    def test_import_multiple_matches(self):

        # to set this test up, we need a slightly more contrived example
        # so I'm going to overwrite gss:E05000148 with gss:E05011464
        div = OrganisationDivision.objects.all().get(
            official_identifier='gss:E05000148'
        )
        div.official_identifier = 'gss:E05011464'
        div.save()
        # this now gives us a situation where we've got 2 divisions
        # in the DB which both have the same GSS code
        # which are members of 2 different DivsionSets:
        self.assertEqual(2,
            OrganisationDivision.objects.all().filter(
                official_identifier='gss:E05011464'
            ).count()
        )


        # if we try to import without the --all flag
        self.opts['code'] = 'gss:E05011464'
        output = self.run_command_with_test_data()
        # this should throw an error and tell us what to do
        self.assertIn('Imported 0 boundaries', output)
        self.assertIn('E05011464: get() returned more than one OrganisationDivision -- it returned 2!', output)
        self.assertIn('To import this boundary against all occurrences of this code, re-run the command with the --all flag', output)
        # and the DB content should not have changed
        self.assertEqual(28, count_divs_by_source('lgbce'))
        self.assertEqual(24, count_divs_by_source('unknown'))
        self.assertEqual(0, count_divs_by_source('imported in unit test'))


        # but if we run it again with the --all flag
        self.opts['all'] = True
        output = self.run_command_with_test_data()
        # this time it should import the boundary
        # against both matching division objects
        self.assertIn('Imported 1 boundaries', output)
        self.assertEqual(27, count_divs_by_source('lgbce'))
        self.assertEqual(23, count_divs_by_source('unknown'))
        self.assertEqual(2, count_divs_by_source('imported in unit test'))

    def test_import_organisation(self):
        # we can import Organisation boundaries as well as divisions
        self.assertEqual('unknown',
            OrganisationGeography.objects.get(gss='E09000008').source
        )
        self.opts['code'] = 'gss:E09000008'
        output = self.run_command_with_test_data()
        self.assertIn('Imported 1 boundaries', output)
        self.assertEqual('imported in unit test',
            OrganisationGeography.objects.get(gss='E09000008').source
        )
