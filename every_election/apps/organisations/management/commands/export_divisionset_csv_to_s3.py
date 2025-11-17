import csv
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.contrib.gis.db.models.functions import AsWKT
from django.core.management.base import BaseCommand, CommandError
from organisations.models.divisions import OrganisationDivisionSet
from storage.s3wrapper import S3Wrapper

CSV_HEADER = [
    "divisionset_id",
    "division_composite_id",
    "division_name",
    "division_slug",
    "division_type",
    "division_subtype",
    "division_official_identifier",
    "division_geography_wkt",
]


class Command(BaseCommand):
    help = "Management command to export a CSV of DivisionSet divisions and their subdivided geographies as WKT to S3."

    def add_arguments(self, parser):
        parser.add_argument(
            "divisionset_id",
            type=int,
            help="ID of the DivisionSet to export.",
        )

        parser.add_argument(
            "--bucket",
            type=str,
            help="S3 bucket to upload the CSV to. Defaults to ee.data-cache.<environment>.",
            default=f"ee.data-cache.{settings.DC_ENVIRONMENT}",
        )
        return super().add_arguments(parser)

    def handle(self, *args, **options):
        s3 = S3Wrapper(options["bucket"])
        divisionset_id = options["divisionset_id"]
        divisionset = self.validate_divisionset_id(divisionset_id)

        with NamedTemporaryFile(mode="w+") as temp_file:
            csv_writer = csv.writer(temp_file)
            csv_writer.writerow(CSV_HEADER)

            for div in divisionset.divisions.all():
                composite_id = f"{divisionset_id}-{div.slug}"
                for subdiv in div.geography.subdivided.values(
                    wkt=AsWKT("geography")
                ):
                    row = [
                        divisionset_id,
                        composite_id,
                        div.name,
                        div.slug,
                        div.division_type,
                        div.division_subtype,
                        div.official_identifier,
                        subdiv["wkt"],
                    ]
                    csv_writer.writerow(row)

            temp_file.flush()
            s3_key = f"divisionsets-with-wkt/{divisionset_id}.csv"
            s3.upload_file_from_fp(temp_file.name, key=s3_key)
            self.stdout.write(
                f"Uploaded divisionset CSV for id {divisionset_id} to {options['bucket']}/{s3_key}."
            )

    def validate_divisionset_id(self, divisionset_id):
        try:
            division_set = OrganisationDivisionSet.objects.prefetch_related(
                "divisions__geography__subdivided"
            ).get(id=divisionset_id)
        except OrganisationDivisionSet.DoesNotExist:
            raise CommandError(
                f"OrganisationDivisionSet with id {divisionset_id} does not exist."
            )

        if not division_set.get_division_geographies().exists():
            raise CommandError(
                f"OrganisationDivisionSet with id '{divisionset_id}' has no division geographies."
            )

        return division_set
