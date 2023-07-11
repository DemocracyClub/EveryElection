"""
Pass in either a directory path to an already extracted
copy of BoundaryLine or a path to a zipped copy.

For example:
manage.py boundaryline_backport_codes -f /foo/bar/bdline_gb-2018-05
manage.py boundaryline_backport_codes -f /foo/bar/bdline_gb-2018-05.zip
manage.py boundaryline_backport_codes -u "http://parlvid.mysociety.org/os/bdline_gb-2018-05.zip"

are all valid calls.

You can use the --show-picker option, but it's sensible to run it first without, as it's then much quicker to tidy up
those that remain.
"""

import argparse
import os
from collections import namedtuple
from datetime import datetime

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import transaction

from organisations.models import Organisation, OrganisationDivision
from organisations.boundaries.boundaryline import BoundaryLine
from organisations.boundaries.constants import get_area_type_lookup
from organisations.boundaries.management.base import BaseBoundaryLineCommand


class Command(BaseBoundaryLineCommand):
    help = """
    Use BoundaryLine to try and retrospectively attach codes
    to divisions imported from LGBCE with pseudo-identifiers.
    """

    WARD_TYPES = ("UTE", "DIW", "LBW", "MTW", "UTW")
    Record = namedtuple("Record", ["division", "code"])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.found = []
        self.not_found = []
        self.org_boundaries = {}

    def add_arguments(self, parser):
        def check_valid_date(value):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                raise argparse.ArgumentTypeError(
                    "Not a valid date: '{0}'.".format(value)
                )

        parser.add_argument(
            "date",
            action="store",
            help="Reference date for BoundaryLine release",
            type=check_valid_date,
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry-run",
            help="Don't commit changes",
        )
        parser.add_argument(
            "--show-picker",
            action="store_true",
            dest="show-picker",
            help="Show picker when requiring manual review",
        )
        super().add_arguments(parser)

    def get_divisions(self, types, date):
        return (
            OrganisationDivision.objects.filter(division_type__in=types)
            .filter_by_date(date)
            .filter_with_temp_id()
            .order_by("official_identifier")
            .select_related("divisionset")
        )

    def get_parent_org_boundary(self, div):
        """
        For performance reasons, we cache these results in a dict indexed by
        (organisation_id, divisionset.start_date)
        This means we only need to do one round-trip to the DB per DivisionSet
        instead of once per division. This speeds things up a bit.
        """
        if (div.organisation_id, div.divisionset.start_date) in self.org_boundaries:
            return self.org_boundaries[
                (div.organisation_id, div.divisionset.start_date)
            ]

        org = Organisation.objects.get(pk=div.organisation_id).get_geography(
            div.divisionset.start_date
        )
        self.org_boundaries[(div.organisation_id, div.divisionset.start_date)] = org
        return org

    @transaction.atomic
    def save_all(self):
        self.stdout.write("Saving...")
        for rec in self.found:
            rec.division.official_identifier = rec.code
            rec.division.save()
        self.stdout.write("...done")

    def report_found(self):
        for rec in self.found:
            self.stdout.write(
                "Found code {code} for division {div}".format(
                    code=rec.code, div=rec.division.official_identifier
                )
            )

    def report_not_found(self):
        for rec in self.not_found:
            self.stdout.write(
                "Could not find a code for division {div}".format(
                    div=rec.division.official_identifier
                )
            )

    def report(self, verbose):
        self.stdout.write(
            "Searched {} divisions".format(len(self.found) + len(self.not_found))
        )
        self.stdout.write("Found {} codes".format(len(self.found)))
        self.stdout.write("\n")
        if verbose:
            self.report_found()
        self.stdout.write("\n")
        self.report_not_found()

    def handle(self, *args, **options):
        base_dir = self.get_base_dir(**options)

        self.stdout.write("Searching...")
        lookup = get_area_type_lookup(filter=lambda x: x in self.WARD_TYPES, group=True)
        for org_type, filename in lookup.items():
            bl = BoundaryLine(
                os.path.join(base_dir, "Data", "GB", filename),
                show_picker=options["show-picker"],
            )
            divs = self.get_divisions(org_type, options["date"])
            for div in divs:
                org = self.get_parent_org_boundary(div)
                try:
                    code = bl.get_division_code(div, org)
                except (MultipleObjectsReturned, ObjectDoesNotExist) as e:
                    self.stdout.write(str(e))
                    code = None
                if code:
                    self.found.append(self.Record(div, code))
                else:
                    self.not_found.append(self.Record(div, code))

        verbose = options["verbosity"] > 1
        self.report(verbose)

        if not options["dry-run"]:
            self.save_all()

        if self.cleanup_required:
            self.cleanup(base_dir)

        self.stdout.write("...done!")
