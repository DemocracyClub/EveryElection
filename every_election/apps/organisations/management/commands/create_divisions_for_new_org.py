from core.mixins import ReadFromCSVMixin
from django.conf import settings
from django.contrib.gis.db.models import Union
from django.core.management import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from organisations.boundaries.helpers import overlap_percent
from organisations.models import (
    DivisionGeography,
    Organisation,
    OrganisationDivision,
    OrganisationDivisionSet,
)


class Command(ReadFromCSVMixin, BaseCommand):
    help = """
    Creates divisions for a new organisation by copying from existing divisions.
    This command should only be used if the new organisation is taking divisions
    which have the same boundaries as existing divisions. Although the new
    divisions can be taken from different existing division sets, and the names
    can be modified, it is assumed that generally all the divisions will be
    directly inherited from a single organisation.

    Takes a CSV file with header: old_divisionset, old_name, new_name, gss, seats_total
    
    - old_divisionset: PK of the source OrganisationDivisionSet
    - old_name: name of the source division
    - new_name: name for the new division
    - gss: GSS code for the new division. If blank will use a temp id.
    - seats_total: number of seats for this division

    Creates a new OrganisationDivisionSet for the organisation and copies
    the specified divisions with their geographies. The new divisionset start_date
    is set to the organisation's start_date.

    Example for East Surrey:
    python manage.py create_divisions_for_new_org \
      -f path/to/east-surrey.csv
      --organisation 123 \
      --division-type UTW \
      --short-title "The Surrey (Structural Changes) Order 2026"
    """

    S3_BUCKET_NAME = settings.LGBCE_BUCKET

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--organisation",
            action="store",
            required=True,
            type=int,
            help="Primary key of the organisation",
        )
        parser.add_argument(
            "--division-type",
            action="store",
            required=True,
            help="Division type for all new divisions (e.g., UTW)",
        )
        parser.add_argument(
            "--legislation-url",
            action="store",
            default="",
            help="Legislation URL for the division set",
        )
        parser.add_argument(
            "--short-title",
            action="store",
            default="",
            help="Short title for the division set",
        )
        parser.add_argument(
            "--ignore-coverage-check",
            action="store_true",
            default=False,
            help="Ignore coverage check failures (use with caution)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.division_type = options["division_type"]
        self.legislation_url = options.get("legislation_url") or ""
        self.short_title = options.get("short_title") or ""
        self.ignore_coverage_check = options.get("ignore_coverage_check", False)

        # Get the new org - this should already be created.
        self.get_new_org(options["organisation"])
        self.start_date = self.new_org.start_date

        # Read the CSV
        division_dicts = self.load_data(options)
        self.stdout.write(f"Found {len(division_dicts)} divisions in CSV")

        # Create the new divisionset
        self.create_divisionset()

        # Create divisions
        self.create_divisions(division_dicts)

        if self.ignore_coverage_check:
            self.stdout.write(self.style.WARNING("Skipping coverage check"))
        else:
            self.coverage_check()

    def get_new_org(self, new_org_pk):
        # Get organisation
        try:
            self.new_org = Organisation.objects.get(pk=new_org_pk)
        except Organisation.DoesNotExist:
            raise CommandError(f"Organisation with pk={new_org_pk} not found")

        # Check that the organisation doesn't already have a divisionset
        if self.new_org.divisionset.exists():
            raise CommandError(
                f"Organisation '{self.new_org.official_identifier}' already has a divisionset. "
                "This command is only for new organisations."
            )

    def create_divisionset(self):
        """Create the new OrganisationDivisionSet."""
        self.divisionset = OrganisationDivisionSet.objects.create(
            organisation=self.new_org,
            start_date=self.start_date,
            legislation_url=self.legislation_url,
            short_title=self.short_title,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Created OrganisationDivisionSet: {self.divisionset}"
            )
        )

    def create_divisions(self, division_dicts):
        # Copy each division
        for division_dict in division_dicts:
            source_div = self.get_source_division(
                division_dict["old_name"], int(division_dict["old_divisionset"])
            )
            new_div = self.copy_division(source_div, division_dict)
            self.stdout.write(f"  Copied: {source_div.name} -> {new_div.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCreated {len(division_dicts)} divisions for {self.new_org.common_name}"
            )
        )

    def get_source_division(self, old_name, old_divisionset_pk):
        """Look up a division by name in the specified divisionset."""
        try:
            return OrganisationDivision.objects.get(
                name=old_name, divisionset_id=old_divisionset_pk
            )
        except OrganisationDivision.DoesNotExist:
            raise CommandError(
                f"Division '{old_name}' not found in divisionset {old_divisionset_pk}"
            )
        except OrganisationDivision.MultipleObjectsReturned:
            raise CommandError(
                f"Multiple divisions named '{old_name}' in divisionset {old_divisionset_pk}"
            )

    def copy_division(self, source_div, division_dict):
        new_name = division_dict["new_name"]
        seats_total = int(division_dict["seats_total"])
        slug = slugify(new_name)
        if division_dict["gss"]:
            official_identifier = f"gss:{division_dict['gss']}"
        else:
            official_identifier = f"{self.new_org.official_identifier}:{slug}"

        new_div = OrganisationDivision.objects.create(
            divisionset=self.divisionset,
            name=new_name,
            official_identifier=official_identifier,
            slug=slug,
            division_type=self.division_type,
            seats_total=seats_total,
            territory_code=source_div.territory_code,
        )

        source_geog = source_div.geography
        DivisionGeography.objects.create(
            division=new_div,
            geography=source_geog.geography,
            source=f"{source_geog.source} via DivisionGeography: {source_geog.id}",
        )

        return new_div

    def coverage_check(self):
        """Check that division geographies cover the organisation geography."""
        div_union = DivisionGeography.objects.filter(
            division__divisionset=self.divisionset
        ).aggregate(Union("geography"))["geography__union"]
        org_geom = self.new_org.geographies.latest().geography

        coverage_percent = overlap_percent(org_geom, div_union)
        if coverage_percent >= 99.99:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Coverage check passed: New divisions cover {coverage_percent:.2f}% of new org"
                )
            )
        elif coverage_percent >= 99:
            self.stdout.write(
                self.style.WARNING(
                    f"Coverage check: New divisions cover {coverage_percent:.2f}% of new org - "
                    "please carry out a visual check of the boundaries"
                )
            )
        else:
            msg = (
                f"Coverage check failed: New divisions cover {coverage_percent:.2f}% of new org -"
                "(threshold: 99%). "
            )
            raise CommandError(
                msg + "Re-run with --ignore-coverage-check to proceed anyway."
            )
