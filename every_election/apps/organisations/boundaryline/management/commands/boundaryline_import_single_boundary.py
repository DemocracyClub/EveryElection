import os
import re
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
        super().add_arguments(parser)

    def get_record(self, identifier):
        # use code to find a matching OrganisationGeography
        # or OrganisationDivision record

        code_type, code = split_code(identifier)

        if code_type == 'unit_id' and re.match(r'^\d+$', code):
            return OrganisationDivision.objects.all().get(official_identifier=identifier)

        if code_type == 'gss' and re.match(r'^[A-Z][0-9]{8}$', code):
            try:
                return OrganisationGeography.objects.all().get(
                    gss=code)
            except OrganisationGeography.DoesNotExist:
                return OrganisationDivision.objects.all().get(
                    official_identifier=identifier)
            except (OrganisationGeography.MultipleObjectsReturned,
                        OrganisationDivision.MultipleObjectsReturned):
                raise

        raise ValueError("Unknown code type. Expected 'gss:X01000001' or 'unit_id:12345'")

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

    def handle(self, *args, **options):
        code = options['code']
        self.source = options['source']

        self.base_dir = self.get_base_dir(**options)
        rec = self.get_record(code)

        self.stdout.write("Importing boundary for area {}...".format(code))
        if type(rec) == OrganisationDivision:
            self.import_div_geography(rec)

        if type(rec) == OrganisationGeography:
            self.import_org_geography(rec)
        self.stdout.write("...done!")
