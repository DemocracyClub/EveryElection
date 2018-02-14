"""
manage.py import_lgbce
  -s S3, --s3 S3        S3 key to import e.g: foo/bar/baz.zip
  -n NAME_COLUMN, --name-column NAME_COLUMN
                        Column in the input file where we should look for
                        division names (default = 'name')
  --srid {27700,4326}   SRID (co-ordinates system) used by the input file
                        (default = 27700)

This command imports boundaries from a shapefile published by LGBCE
and attaches them to Divisions (based on name match) from the most recent
DivisionSet with a NULL end date.

manage.py import_lgbce FOO -s "foo/bar/baz.zip"
"""


import json
import os
import shutil
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.core.management.base import BaseCommand
from organisations.importers import DivisionSetGeographyImporter, DiffException
from organisations.models import Organisation, OrganisationDivisionSet
from storage.s3wrapper import S3Wrapper
from storage.zipfile import unzip


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'org',
            action='store',
            help='3-letter organisation code e.g: KHL'
        )
        parser.add_argument(
            '-s',
            '--s3',
            required=True,
            action='store',
            help='S3 key to import e.g: foo/bar/baz.zip'
        )
        parser.add_argument(
            '-n',
            '--name-column',
            help="Column in the input file where we should look for division names (default = 'name')",
            default='name'
        )
        parser.add_argument(
            '--srid',
            help="SRID (co-ordinates system) used by the input file (default = 27700)",
            default="27700",
            choices=["27700", "4326"]
        )

    def handle(self, *args, **options):
        srid = int(options['srid'])
        divset = self.get_division_set(options['org'])

        try:
            (tempdir, data) = self.get_data(options['s3'])
            name_map = self.get_name_map(options['s3'])
            self.import_data(data, divset, options['name_column'], name_map, srid)
        except Exception:
            # if anything throws an unhandled error,
            # try to clean up the temp files first
            self.cleanup(tempdir)
            # .. and then we can crash out
            raise

        self.cleanup(tempdir)

    def import_data(self, data, divset, name_column, name_map, srid):
        importer = DivisionSetGeographyImporter(data, divset, name_column, name_map, srid)
        try:
            importer.import_data()
        except DiffException as e:
            errorstr = ''
            errorstr += 'Failed: ' + str(e) + '\n\n'
            errorstr += '\n'.join(e.diff)
            errorstr += "\n\nTo specify fixes names, upload a file 'name_map.json' "
            errorstr += 'with the structure:\n'
            errorstr += '{\n  "oldname1": "newname1",\n  "oldname2": "newname2"\n}'
            self.stderr.write(errorstr)

    def get_data(self, filepath):
        s3 = S3Wrapper(settings.LGBCE_BUCKET)
        f = s3.get_file(filepath)
        tempdir = unzip(f.name)
        ds = DataSource(tempdir)
        return (tempdir, ds)

    def get_name_map(self, filepath):
        s3 = S3Wrapper(settings.LGBCE_BUCKET)
        basepath = os.path.split(filepath)[0]
        try:
            # we specify corrections to names in the LGBCE shapefiles
            # by adding a name_map.json file to the same S3 directory
            # where the shape files are saved
            f = s3.get_file(basepath + '/name_map.json')
            return json.load(open(f.name))
        except ClientError as e:
            if int(e.response['Error']['Code']) == 404:
                # if we didn't find any name map file, return an empty map
                # i.e: just assume the names in the file are correct
                return {}
            else:
                # re-throw any other error
                raise

    def get_division_set(self, org_code):
        org = Organisation.objects.get(official_identifier=org_code)
        divset = OrganisationDivisionSet.objects\
            .filter(organisation=org)\
            .latest()

        # divset is the DivisionSet with the most recent start date
        if not divset.divisions.all():
            error = "Candidate DivisionSet '%s' has no Divisions. Can not import boundaries" % (divset)
            raise Exception(error)

        if divset.has_related_geographies:
            error = "Candidate DivisionSet '%s' already has related Geographies. Can not import boundaries" % (divset)
            raise Exception(error)

        if divset.end_date:
            error = "Candidate DivisionSet '%s' already has end_date %s. Expected NULL" % (divset, divset.end_date)
            raise Exception(error)

        """
        If we got to here, divset satisfies the following criteria:
        - It has the most recent start date
        - It has a NULL end date
        - It has related Divisions
        - It does not have related DivisionGeographies
        so its a pretty safe bet to assume this is the DivisionSet
        we want to import boundaries against.

        TODO: we could also allow the user to manually specify a DivisionSet
        as a command line argument in case we wanted to override this logic
        (e.g: importing historic boundaries)
        """
        return divset

    def cleanup(self, tempdir):
        # clean up the temp files we created
        try:
            shutil.rmtree(tempdir)
        except OSError:
            self.stdout.write("Failed to clean up temp files.")
            self.stdout.write("Oh well. ¯\_(ツ)_/¯ All the important stuff worked.")
