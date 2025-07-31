from django.contrib.gis.gdal import DataSource
from django.db import transaction
from django.utils.text import slugify
from organisations.boundaries.management.base import BaseBoundaryLineCommand
from organisations.models.divisions import (
    DivisionGeography,
    OrganisationDivision,
    OrganisationDivisionSet,
)
from organisations.models.organisations import Organisation
from storage.shapefile import pre_process_layer


class Command(BaseBoundaryLineCommand):
    help = """
    Import Scottish Parliament boundaries from Boundaries Scotland shapefiles. There are two shapefiles: one for regions and one for constituencies.
    These need to be imported separately.
    Use the --regions flag to import regions, or the --constituencies flag to import constituencies.
    """

    def __init__(self, *args, **options):
        super().__init__(*args, **options)
        self.source = "Boundaries Scotland"
        self.srid = 27700
        self.division_type = "SPC"
        self.division_subtype = "Scottish Parliament constituency"
        self.seats_total = 1

    def add_arguments(self, parser):
        super().add_arguments(parser)
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--regions",
            action="store_true",
            dest="regions",
            help="Import Scottish Parliament regions",
        )
        group.add_argument(
            "--constituencies",
            action="store_true",
            dest="constituencies",
            help="Import Scottish Parliament constituencies",
        )

    @transaction.atomic()
    def handle(self, *args, **options):
        self.div_set = self.get_sp_divisionset()
        if options.get("regions"):
            self.division_type = "SPE"
            self.division_subtype = "Scottish Parliament region"
            self.seats_total = 7

        self.stdout.write(self.style.SUCCESS("Starting boundary import..."))
        base_dir = self.get_base_dir(**options)
        layer = self.get_processed_layer(base_dir)

        for f in layer:
            div = self.create_division(f)
            self.create_division_geography(f, div)

        if self.cleanup_required:
            self.cleanup(base_dir)

        self.stdout.write(self.style.SUCCESS("Boundary import completed."))

    def create_division_geography(self, feature, div):
        return DivisionGeography.objects.create(
            division=div,
            geography=feature.multipolygon,
            source=self.source,
        )

    def create_division(self, feature):
        name = feature.get("Name")
        slug = slugify(name)
        identifier = f"sp:{slug}"

        return OrganisationDivision.objects.create(
            official_identifier=identifier,
            temp_id=identifier,
            name=name,
            slug=slug,
            division_type=self.division_type,
            division_subtype=self.division_subtype,
            seats_total=self.seats_total,
            divisionset=self.div_set,
            territory_code="SCT",
        )

    def get_processed_layer(self, base_dir):
        ds = DataSource(base_dir)
        return pre_process_layer(ds[0], self.srid)

    def get_sp_divisionset(self):
        sp = Organisation.objects.get(official_identifier="sp")

        div_set, _ = OrganisationDivisionSet.objects.update_or_create(
            organisation=sp,
            start_date="2026-05-07",
            short_title="2026 Boundaries",
            consultation_url="https://boundaries.scot/reviews/second-review-scottish-parliament-boundaries",
        )

        return div_set
