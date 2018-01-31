import os
import tempfile
from io import StringIO
from django.contrib.gis.gdal import DataSource
from django.utils.text import slugify
from django.test import TestCase
from organisations.models import (DivisionGeography,
    Organisation, OrganisationDivision, OrganisationDivisionSet)
from organisations.management.commands.import_lgbce import Command


class ImportLgbceTests(TestCase):

    def setUp(self):
        self.test_data_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'test_data',
            'test_shapefile',
            'test_shapefile.shp'
        )

        # an org with no division set
        self.org1 = Organisation.objects.create(
            official_identifier='TEST1',
            organisation_type='local-authority',
            official_name="Test Council 1",
            gss="X00000001",
            slug="test1",
            territory_code="ENG",
            election_name="Test Council 1 Local Elections",
        )

        # valid org/div
        self.valid_org_code = 'TEST2'
        valid_org = Organisation.objects.create(
            official_identifier=self.valid_org_code,
            organisation_type='local-authority',
            official_name="Test Council 2",
            gss="X00000006",
            slug="test2",
            territory_code="ENG",
            election_name="Test Council 2 Local Elections",
        )
        self.valid_divset = OrganisationDivisionSet.objects.create(
            organisation=valid_org,
            start_date='2004-12-02',
            end_date=None,
            legislation_url='',
            consultation_url='',
            short_title='',
            mapit_generation_id='',
            notes='',
        )
        division_names = [
            'Furley',
            'Bybrook',
            'Conningbrook & Little Burton Farm',
            'Bockhanger',
            'Kennington'
        ]
        for division_name in division_names:
            OrganisationDivision.objects.create(
                official_identifier=division_name,
                organisation=valid_org,
                divisionset=self.valid_divset,
                geography_curie=division_name,
                name=division_name,
                slug=slugify(division_name),
                division_type='DIW',
                seats_total=1
            )

    def run_import_with_test_data(self, org, name_map):
        cmd = Command()
        cmd.get_data = lambda x: (tempfile.mkdtemp(), DataSource(self.test_data_path))
        cmd.get_name_map = lambda x: name_map
        args = {
            'org': org,
            'file': 'foo.bar/baz',
            'name_column': 'Ward_name',
            'srid': '27700',
        }
        cmd.stderr = StringIO()
        cmd.handle(**args)
        cmd.stderr.seek(0)
        error_output = cmd.stderr.read()
        return error_output

    def test_org_not_found(self):
        with self.assertRaises(Organisation.DoesNotExist):
            self.run_import_with_test_data('NOT-AN-ORG', {})

    def test_divset_not_found(self):
        with self.assertRaises(OrganisationDivisionSet.DoesNotExist):
            self.run_import_with_test_data('TEST1', {})

    def test_divset_has_no_divisions(self):
        # add an empty division set to org1
        OrganisationDivisionSet.objects.create(
            organisation=self.org1,
            start_date='2004-12-02',
            end_date=None,
            legislation_url='',
            consultation_url='',
            short_title='',
            mapit_generation_id='',
            notes='',
        )

        with self.assertRaises(Exception):
            self.run_import_with_test_data('TEST1', {})

    def test_divset_has_end_date(self):
        # divset has divisions and no related geographies but has end date

        # normally this setup would import fine, but we're going to
        # set an end date on the division set so it should fail
        self.valid_divset.end_date = '2018-05-02'
        self.valid_divset.save()

        with self.assertRaises(Exception):
            self.run_import_with_test_data(self.valid_org_code, {})

    def test_names_dont_match(self):
        # there's some names in the test file that don't match the ones in the database
        # but we'll pass an empty name_map - this should cause a failure
        name_map = {}
        error_output = self.run_import_with_test_data(self.valid_org_code, name_map)
        self.assertEqual(
            "Failed: legislation_names != boundary_names", error_output[:43])

    def test_valid(self):
        # all data is valid - should import cleanly

        # this time we'll pass a name_map so all the areas can import
        name_map =  {
            'Conningbrook and Little Burton Farm': 'Conningbrook & Little Burton Farm'
        }
        self.run_import_with_test_data(self.valid_org_code, name_map)

        # ensure all of our divisions now have a geography attached to them
        count = 0
        for d in self.valid_divset.divisions.all():
            try:
                d.geography
                count = count + 1
            except DivisionGeography.DoesNotExist:
                pass
        self.assertEqual(5, count)

    def test_divisionset_has_related_geographies(self):
        name_map =  {
            'Conningbrook and Little Burton Farm': 'Conningbrook & Little Burton Farm'
        }
        self.run_import_with_test_data(self.valid_org_code, name_map)

        # now that we've imported geographies for this divisionset once,
        # if we try to do it again then it should fail
        # because the divisionset has related geographies now
        with self.assertRaises(Exception):
            self.run_import_with_test_data(self.valid_org_code, name_map)
