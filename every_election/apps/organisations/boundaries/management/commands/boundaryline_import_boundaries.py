"""
Import a single boundary based on identifier
Also pass a --source flag indicating where the boundary came from

The --all flag may also optionally be passed if a code exists in multiple
DivisionSets and we want to import the boundary against all occurrences.

Example calls:
manage.py boundaryline_import_boundaries --code gss:W09000043 --source bdline_gb-2018-05 -f /foo/bar/bdline_gb-2018-05
manage.py boundaryline_import_boundaries --code gss:W09000019 --source bdline_gb-2018-05 --all -u "http://parlvid.mysociety.org/os/bdline_gb-2018-05.zip"
manage.py boundaryline_import_boundaries --codes /foo/bar/codes.json --source bdline_gb-2018-05 -f /foo/bar/bdline_gb-2018-05
"""

import json
import os
import re

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from organisations.boundaries.boundaryline import BoundaryLine
from organisations.boundaries.constants import (
    SPECIAL_CASES,
    get_area_type_lookup,
)
from organisations.boundaries.helpers import split_code
from organisations.boundaries.management.base import BaseBoundaryLineCommand
from organisations.constants import REGISTER_SUBTYPE_TO_BOUNDARYLINE_TYPE
from organisations.models import (
    DivisionGeography,
    OrganisationDivision,
    OrganisationGeography,
)
from storage.shapefile import convert_geom_to_multipolygon


class Command(BaseBoundaryLineCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.errors = []

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--code",
            action="store",
            help="code in the form gss:X01000001 or unit_id:12345",
        )
        group.add_argument(
            "--codes",
            action="store",
            help="local path to a JSON file containing an array of codes",
        )

        parser.add_argument(
            "--source",
            action="store",
            help="where did this boundary come from? e.g: bdline_gb-2018-05",
            required=True,
        )
        parser.add_argument(
            "--all",
            action="store_true",
            dest="all",
            help="import boundaries against multiple GSS codes if found",
        )
        super().add_arguments(parser)

    def validate_identifier(self, identifier):
        # throw an exception if we're going to have a bad time with this id
        # return True if it looks good
        code_type, code = split_code(identifier)

        if code_type == "unit_id" and re.match(r"^\d+$", code):
            # FIXME before 2021
            error = (
                "Importing boundaries from BoundaryLine against CEDs is "
                "not yet available because unit_id is not a stable identifier"
            )
            raise ValueError(error)

        if code_type == "gss" and re.match(r"^[A-Z][0-9]{8}$", code):
            return True

        raise ValueError(
            "Unknown code type. Expected 'gss:X01000001' or 'unit_id:12345'"
        )

    def filter_records(self, identifier):
        # use code to find matching OrganisationGeography
        # or OrganisationDivision records

        _, code = split_code(identifier)

        orgs = OrganisationGeography.objects.all().filter(gss=code)
        if orgs.exists():
            return orgs

        divs = OrganisationDivision.objects.all().filter(
            official_identifier=identifier
        )
        if divs.exists():
            return divs

        raise ObjectDoesNotExist(
            (
                "Couldn't find any OrganisationGeography or OrganisationDivision "
                "objects matching {}".format(identifier)
            )
        )

    def get_record(self, identifier):
        # use code to find a matching OrganisationGeography
        # or OrganisationDivision record

        _, code = split_code(identifier)
        try:
            return OrganisationGeography.objects.all().get(gss=code)
        except OrganisationGeography.DoesNotExist:
            return OrganisationDivision.objects.all().get(
                official_identifier=identifier
            )

    def get_geography_from_feature(self, feature):
        # extract a geography object we can safely save to
        # our database from a BoundaryLine feature record
        geom = convert_geom_to_multipolygon(feature)
        geom.srid = 27700
        geom.transform(4326)
        return geom

    def open_boundaryline(self, area_type):
        # work out which shapefile we need to open for this area_type and
        # return a BoundaryLine object giving us an abstraction over it
        lookup = get_area_type_lookup()
        filename = lookup[area_type]
        return BoundaryLine(os.path.join(self.base_dir, "Data", "GB", filename))

    def import_org_geography(self, org_geo):
        if org_geo.gss in SPECIAL_CASES:
            filename = SPECIAL_CASES[org_geo.gss]["file"]
            proxy_code = SPECIAL_CASES[org_geo.gss]["code"]
            bl = BoundaryLine(
                os.path.join(self.base_dir, "Data", "GB", filename)
            )
            geom = self.get_geography_from_feature(
                bl.get_feature_by_field("code", proxy_code)
            )
        else:
            area_type = REGISTER_SUBTYPE_TO_BOUNDARYLINE_TYPE[
                org_geo.organisation.organisation_subtype
            ]
            bl = self.open_boundaryline(area_type)
            geom = self.get_geography_from_feature(
                bl.get_feature_by_field("code", org_geo.gss)
            )

        org_geo.geography = geom.ewkb
        org_geo.source = self.source
        org_geo.save()
        self.stdout.write("..saved {}".format(str(org_geo)))

    def import_div_geography(self, div):
        area_type = div.division_type
        bl = self.open_boundaryline(area_type)
        code_type, code = split_code(div.official_identifier)
        fieldname = "code" if code_type == "gss" else code_type
        geom = self.get_geography_from_feature(
            bl.get_feature_by_field(fieldname, code)
        )

        try:
            div.geography.geography = geom.ewkb
            div.geography.source = self.source
            div.geography.save()
        except DivisionGeography.DoesNotExist:
            dg = DivisionGeography(
                division_id=div.id, geography=geom.ewkb, source=self.source
            )
            dg.save()
        self.stdout.write("..saved {}".format(str(div)))

    def import_record(self, record):
        if type(record) == OrganisationDivision:
            self.import_div_geography(record)

        if type(record) == OrganisationGeography:
            self.import_org_geography(record)

    def import_all(self, identifiers, allow_multiple):
        for identifier in identifiers:
            self.validate_identifier(identifier)

        for identifier in identifiers:
            self.stdout.write(
                "Importing boundary for area {}...".format(identifier)
            )

            try:
                records = self.get_records(identifier, allow_multiple)
                for rec in records:
                    self.import_record(rec)
            except (ObjectDoesNotExist, MultipleObjectsReturned) as e:
                self.stdout.write("..FAILED!")
                self.errors.append((identifier, e))
                continue

    def get_records(self, identifier, allow_multiple):
        if allow_multiple:
            records = self.filter_records(identifier)
        else:
            try:
                records = [self.get_record(identifier)]
            except (
                OrganisationGeography.MultipleObjectsReturned,
                OrganisationDivision.MultipleObjectsReturned,
            ) as e:
                message = str(e) + (
                    " This might indicate a problem which needs to be fixed, "
                    "but it can also be valid for the same GSS code to appear "
                    "in more than one DivisionSet. "
                    "To import this boundary against all occurrences "
                    "of this code, re-run the command with the --all flag"
                )
                raise MultipleObjectsReturned(message)
        return records

    def get_identifiers(self, options):
        if options["code"]:
            return [options["code"]]
        with open(options["codes"]) as f:
            codes = json.load(f)
        if not isinstance(codes, (list,)):
            raise ValueError("Root JSON element must be array []")
        return codes

    def handle(self, *args, **options):
        identifiers = self.get_identifiers(options)
        self.source = options["source"]
        self.base_dir = self.get_base_dir(**options)

        self.import_all(identifiers, options["all"])

        self.stdout.write("\n\n")
        self.stdout.write(
            "Imported {} boundaries.\n\n".format(
                len(identifiers) - len(self.errors)
            )
        )
        self.stdout.write("{} Failures:".format(len(self.errors)))
        for identifier, e in self.errors:
            self.stdout.write(
                "{id}: {error}".format(id=identifier, error=str(e))
            )

        if self.cleanup_required:
            self.cleanup(self.base_dir)

        self.stdout.write("...done!")

        if self.cleanup_required:
            self.cleanup(self.base_dir)

        self.stdout.write("...done!")
