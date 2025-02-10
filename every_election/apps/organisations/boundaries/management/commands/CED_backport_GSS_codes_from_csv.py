"""
Pass in either a directory path or a download link to an ONS csv e.g.
Ward to LAD to County to County Electoral Division (May 2024) Lookup for EN

example calls:
manage.py CED_backport_GSS_codes_from_csv -f /foo/bar/Ward_to_LAD_to_County_to_CED_(May_2024)_Lookup.csv
manage.py boundaryline_backport_codes -u "https://hub.arcgis.com/api/v3/datasets/foo/downloads/data?format=csv&spatialRefId=bar&where=foo"

"""

import json
import re
from collections import namedtuple

from core.mixins import ReadFromCSVMixin
from django.core.management.base import BaseCommand
from django.db import transaction
from organisations.boundaries.helpers import (
    normalize_name_for_matching,
)
from organisations.models import OrganisationDivision


class Command(ReadFromCSVMixin, BaseCommand):
    help = """
        Tries to backport GSS codes from a CSV file to the codeless CEDs in the database.
        Defaults to current (end_date=null) CEDS that do not have gss codes.
    """
    Match = namedtuple("Match", ["division", "code"])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.found = []
        self.not_found = []

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--divset-id",
            action="store",
            dest="divset-id",
            help="divisionset id to match against",
        )
        group.add_argument(
            "--divset-ids",
            action="store",
            dest="divset-ids",
            help="local path to a JSON file containing an array of divisonset ids to match against",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry-run",
            help="Don't commit changes",
        )
        super().add_arguments(parser)

    def handle(self, *args, **options):
        csv_data = self.load_data(options)

        self.stdout.write("Processing csv...")
        col_names = self.extract_col_names(csv_data)
        lookup = self.create_csv_lookup(csv_data, col_names)

        ceds = self.get_ceds_to_match(options)

        self.match_db_ceds_to_csv_ceds(lookup, ceds)

        if not options["dry-run"]:
            self.save_all()

        verbose = options["verbosity"] > 1
        self.report(verbose, lookup)

    def report_found(self):
        for match in self.found:
            self.stdout.write(
                f"Found code {match.code} for division id: {match.division.id}"
            )

    def report_not_found(self):
        for division in self.not_found:
            self.stdout.write(
                f"Could not find a code for division id: {division.id}"
            )

    def report(self, verbose, lookup):
        self.stdout.write(
            f"Found {len(lookup)} unique GSS codes in the input file."
        )
        self.stdout.write(
            f"Searched {len(self.found) + len(self.not_found)} divisions"
        )
        self.stdout.write(f"Matched {len(self.found)} codes")
        self.stdout.write("\n")
        if verbose:
            self.report_found()
        self.stdout.write("\n")
        self.report_not_found()

    @transaction.atomic
    def save_all(self):
        self.stdout.write("Saving...")
        for match in self.found:
            match.division.official_identifier = match.code
            match.division.save()
        self.stdout.write("...done")

    def match_db_ceds_to_csv_ceds(self, lookup, ceds):
        for division in ceds:
            division_name = division.slug
            division_county = division.divisionset.organisation.slug

            match_found = False

            key = (division_name, division_county)
            if key in lookup:
                self.found.append(self.Match(division, f"gss:{lookup[key]}"))
                match_found = True

            if not match_found:
                self.not_found.append(division)

    def extract_col_names(self, csv_data):
        col_names = {}
        first_row = csv_data[0]
        col_names["ced_name"] = self.match_col_name(first_row, r"CED\d{2}NM")
        col_names["county_name"] = self.match_col_name(first_row, r"CTY\d{2}NM")
        col_names["ced_gss"] = self.match_col_name(first_row, r"CED\d{2}CD")

        return col_names

    def match_col_name(self, data_row, col_regex):
        match = [key for key in data_row if re.match(col_regex, key)]
        if not match:
            raise ValueError(f"No column found matching regex {col_regex} ")
        if len(match) > 1:
            raise ValueError(
                f"Multiple columns foundmatching regex {col_regex}"
            )
        return match[0]

    def create_csv_lookup(self, csv_data, cols):
        lookup = {}
        for line in csv_data:
            ced_name = normalize_name_for_matching(line[cols["ced_name"]])
            county_name = normalize_name_for_matching(line[cols["county_name"]])
            ced_gss = line[cols["ced_gss"]]
            key = (ced_name, county_name)
            if key in lookup and lookup[key] != ced_gss:
                raise Exception("Unexpected error in input file")

            lookup[key] = ced_gss

        return lookup

    def get_ceds_to_match(self, options):
        if options["divset-ids"]:
            with open(options["divset-ids"], "r") as f:
                divset_ids = json.load(f)
                return self.get_ceds().filter(divisionset_id__in=divset_ids)
        return self.get_ceds().filter(divisionset_id=options["divset-id"])

    def get_ceds(self):
        return OrganisationDivision.objects.filter(division_type="CED")
