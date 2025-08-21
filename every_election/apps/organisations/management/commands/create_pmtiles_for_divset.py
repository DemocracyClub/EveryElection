import os
import tempfile

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from organisations.models import OrganisationDivisionSet
from organisations.pmtiles_creator import PMtilesCreator


class Command(BaseCommand):
    help = "Create a pmtiles file for a given divisionset using ogr2ogr and tippecanoe"

    def add_arguments(self, parser):
        parser.add_argument(
            "divisionset_id",
            type=int,
            help="The ID of the divisionset to generate the pmtiles file from",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing pmtiles file if it exists",
        )

    def handle(self, *args, **options):
        using_s3 = False
        divset_id = options["divisionset_id"]
        # Check divset exists
        try:
            divset = OrganisationDivisionSet.objects.get(id=divset_id)
        except OrganisationDivisionSet.DoesNotExist:
            raise CommandError(
                f"OrganisationDivisionSet with id '{divset_id}' does not exist."
            )

        # Use S3 if PUBLIC_DATA_BUCKET is set
        if getattr(settings, "PUBLIC_DATA_BUCKET", None):
            s3_client = boto3.client("s3")
            using_s3 = True
        else:
            # Make pmtiles storage directory in static
            static_path = f"{settings.STATIC_ROOT}/pmtiles-store"
            os.makedirs(static_path, exist_ok=True)

        # Check divset has divisions
        if divset.divisions.count() == 0:
            raise CommandError(
                f"OrganisationDivisionSet with id '{divset_id}' has no divisions."
            )

        # Check for existing file
        if divset.has_pmtiles_file:
            if options["overwrite"] and using_s3:
                s3_client.delete_object(
                    Bucket=settings.PUBLIC_DATA_BUCKET,
                    Key=divset.pmtiles_s3_key,
                )
            elif options["overwrite"] and not using_s3:
                os.remove(f"{static_path}/{divset.pmtiles_file_name}")
            else:
                warning = f"{divset.pmtiles_file_name} already exists{' on S3' if using_s3 else ' locally'}. Skipping (use --overwrite to force)."
                self.stdout.write(self.style.WARNING(warning))
                return

        pmtile_creator = PMtilesCreator(divset)
        with tempfile.TemporaryDirectory() as temp_dir:
            pmtile_fp = pmtile_creator.create_pmtile(temp_dir)

            if using_s3:
                s3_key = divset.pmtiles_s3_key
                s3_client.upload_file(
                    pmtile_fp, settings.PUBLIC_DATA_BUCKET, s3_key
                )
                self.stdout.write(
                    self.style.SUCCESS(f"PMTile uploaded to S3 at {s3_key}.")
                )
            else:
                # Move the pmtiles file to the static directory
                os.rename(
                    pmtile_fp, f"{static_path}/{divset.pmtiles_file_name}"
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"PMTile created at {static_path}/{divset.pmtiles_file_name}."
                    )
                )
