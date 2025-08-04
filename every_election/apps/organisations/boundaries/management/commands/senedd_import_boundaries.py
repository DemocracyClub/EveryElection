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
    Import Senedd boundaries from Democracy and Boundary Commission Cymru.
    """

    def __init__(self, *args, **options):
        super().__init__(*args, **options)
        self.source = "dbcc"
        self.srid = 27700

    @transaction.atomic()
    def handle(self, *args, **options):
        self.div_set = self.get_senedd_divisionset()

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
        name = feature.get("English_Na")
        slug = slugify(name)
        identifier = f"senedd:{slug}"

        return OrganisationDivision.objects.create(
            official_identifier=identifier,
            temp_id=identifier,
            name=name,
            slug=slug,
            division_type="WAC",
            division_subtype="Welsh Assembly constituency",
            seats_total=6,
            divisionset=self.div_set,
            territory_code="WLS",
        )

    def get_processed_layer(self, base_dir):
        ds = DataSource(base_dir)
        return pre_process_layer(ds[0], self.srid)

    def get_senedd_divisionset(self):
        senedd = Organisation.objects.get(official_identifier="senedd")

        return OrganisationDivisionSet.objects.create(
            organisation=senedd,
            start_date="2026-05-07",
            short_title="2026 Boundaries",
            consultation_url="https://www.dbcc.gov.wales/reviews/03-25/2026-review-final-determinations",
        )
