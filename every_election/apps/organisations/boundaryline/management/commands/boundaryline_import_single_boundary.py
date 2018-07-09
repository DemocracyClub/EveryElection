"""
Import a single boundary based on identifier
Also pass a --source flag indicating where the boundary came from

The --all flag may also optionally be passed if a code exists in multiple
DivisionSets and we want to import the boundary against all occurrences.

Example calls:
manage.py boundaryline_import_single_boundary gss:W09000043 --source bdline_gb-2018-05 -f /foo/bar/bdline_gb-2018-05
manage.py boundaryline_import_single_boundary gss:W09000019 --source bdline_gb-2018-05 --all -u "http://parlvid.mysociety.org/os/bdline_gb-2018-05.zip"
"""

import os
import re
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from organisations.models import (
    DivisionGeography,
    OrganisationGeography,
    OrganisationDivision
)
from organisations.boundaryline import BoundaryLine
from organisations.boundaryline.constants import get_area_type_lookup
from organisations.boundaryline.management.base import BaseBoundaryLineCommand
from organisations.boundaryline.helpers import split_code
from organisations.constants import REGISTER_SUBTYPE_TO_BOUNDARYLINE_TYPE
from storage.shapefile import convert_geom_to_multipolygon


class Command(BaseBoundaryLineCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'code',
            action='store',
            help='code in the form gss:X01000001 or unit_id:12345',
        )
        parser.add_argument(
            '--source',
            action='store',
            help='where did this boundary come from? e.g: bdline_gb-2018-05',
            required=True,
        )
        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            help='import this boundary against multiple GSS codes if found',
        )
        super().add_arguments(parser)

    def validate_identifier(self, identifier):
        # throw an exception if we're going to have a bad time with this id
        # return True if it looks good
        code_type, code = split_code(identifier)

        if code_type == 'unit_id' and re.match(r'^\d+$', code):
            # FIXME before 2021
            error = ("Importing boundaries from BoundaryLine against CEDs is "
            "not yet available because unit_id is not a stable identifier")
            raise ValueError(error)

        if code_type == 'gss' and re.match(r'^[A-Z][0-9]{8}$', code):
            return True

        raise ValueError("Unknown code type. Expected 'gss:X01000001' or 'unit_id:12345'")

    def filter_records(self, identifier):
        # use code to find matching OrganisationGeography
        # or OrganisationDivision records

        self.validate_identifier(identifier)
        _, code = split_code(identifier)

        orgs = OrganisationGeography.objects.all().filter(gss=code)
        if orgs.exists():
            return orgs

        divs = OrganisationDivision.objects.all().filter(
            official_identifier=identifier)
        if divs.exists():
            return divs

        raise ObjectDoesNotExist(
            ("Couldn't find any OrganisationGeography or OrganisationDivision "
            "objects matching {}".format(identifier))
        )

    def get_record(self, identifier):
        # use code to find a matching OrganisationGeography
        # or OrganisationDivision record

        self.validate_identifier(identifier)
        _, code = split_code(identifier)
        try:
            return OrganisationGeography.objects.all().get(
                gss=code)
        except OrganisationGeography.DoesNotExist:
            return OrganisationDivision.objects.all().get(
                official_identifier=identifier)

    def get_geography_from_feature(self, feature):
        # extract a geography object we can safely save to
        # our database from a BoundaryLine feature record
        geom = convert_geom_to_multipolygon(feature.geom.geos)
        geom.srid=27700
        geom.transform(4326)
        return geom

    def open_boundaryline(self, area_type):
        # work out which shapefile we need to open for this area_type and
        # return a BoundaryLine object giving us an abstraction over it
        lookup = get_area_type_lookup()
        filename = lookup[area_type]
        return BoundaryLine(os.path.join(self.base_dir, 'Data', 'GB', filename))

    def import_org_geography(self, org_geo):
        area_type = REGISTER_SUBTYPE_TO_BOUNDARYLINE_TYPE[org_geo.organisation.organisation_subtype]
        bl = self.open_boundaryline(area_type)
        geom = self.get_geography_from_feature(bl.get_feature_by_field('code', org_geo.gss))
        org_geo.geography = geom
        org_geo.source = self.source
        org_geo.save()
        self.stdout.write('..saved {}'.format(str(org_geo)))

    def import_div_geography(self, div):
        area_type = div.division_type
        bl = self.open_boundaryline(area_type)
        code_type, code = split_code(div.official_identifier)
        fieldname = 'code' if code_type == 'gss' else code_type
        geom = self.get_geography_from_feature(bl.get_feature_by_field(fieldname, code))

        try:
            div.geography.geography = geom.ewkb
            div.geography.source = self.source
            div.geography.save()
        except DivisionGeography.DoesNotExist:
            dg = DivisionGeography(
                division_id=div.id,
                geography=geom.ewkb,
                source=self.source
            )
            dg.save()
        self.stdout.write('..saved {}'.format(str(div)))

    def import_record(self, record):
        if type(record) == OrganisationDivision:
            self.import_div_geography(record)

        if type(record) == OrganisationGeography:
            self.import_org_geography(record)

    def handle(self, *args, **options):
        code = options['code']
        self.source = options['source']

        self.base_dir = self.get_base_dir(**options)

        if options['all']:
            records = self.filter_records(code)
        else:
            try:
                records = [self.get_record(code)]
            except (OrganisationGeography.MultipleObjectsReturned,
                        OrganisationDivision.MultipleObjectsReturned) as e:
                message = str(e) + "\n\n" + (
                    "This might indicate a problem which needs to be fixed, "
                    "but it can also be valid for the same GSS code to appear "
                    "in more than one DivisionSet.\n\n"
                    "To import this boundary against all occurrences "
                    "of this code, re-run the command with the --all flag"
                )
                raise MultipleObjectsReturned(message)

        self.stdout.write("Importing boundary for area {}...".format(code))
        for rec in records:
            self.import_record(rec)

        if self.cleanup_required:
            self.cleanup(self.base_dir)

        self.stdout.write("...done!")
