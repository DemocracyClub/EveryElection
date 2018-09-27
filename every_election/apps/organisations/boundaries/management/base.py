import shutil

from django.core.management.base import BaseCommand
from core.mixins import ReadFromFileMixin
from organisations.models import (
    DivisionGeography,
    OrganisationDivision,
    OrganisationGeography,
)
from storage.zipfile import unzip


class BaseBoundaryLineCommand(ReadFromFileMixin, BaseCommand):

    def get_base_dir(self, **options):
        self.cleanup_required = False
        try:
            if options['url']:
                self.stdout.write('Downloading data from %s ...' % (options['url']))
            fh = self.load_data(options)
            self.stdout.write('Extracting archive...')
            path = unzip(fh.name)
            self.stdout.write('...done')

            # if we've extracted a zip file to a temp location
            # we want to delete the temp files when we're done
            self.cleanup_required = True
            return path
        except IsADirectoryError:
            return options['file']

    def cleanup(self, tempdir):
        # clean up the temp files we created
        try:
            shutil.rmtree(tempdir)
        except OSError:
            self.stdout.write("Failed to clean up temp files.")


class BaseOsniCommand(BaseCommand):

    def __init__(self, *args, **options):
        self.source = 'OSNIOpenData_LargescaleBoundaries'
        super().__init__(*args, **options)

    def import_boundary(self, record, feature):
        if type(record) == OrganisationDivision:
            self.import_div_geography(record, feature)

        if type(record) == OrganisationGeography:
            self.import_org_geography(record, feature)

    def import_org_geography(self, org_geo, feature):
        org_geo.geography = feature['geometry'].ewkb
        org_geo.source = self.source
        org_geo.save()
        self.stdout.write(
            "Importing boundary for area {}...saved".format(str(org_geo)))

    def import_div_geography(self, div, feature):
        try:
            div.geography.geography = feature['geometry'].ewkb
            div.geography.source = self.source
            div.geography.save()
        except DivisionGeography.DoesNotExist:
            dg = DivisionGeography(
                division_id=div.id,
                geography=feature['geometry'].ewkb,
                source=self.source
            )
            dg.save()
        self.stdout.write(
            "Importing boundary for area {}...saved".format(str(div)))
