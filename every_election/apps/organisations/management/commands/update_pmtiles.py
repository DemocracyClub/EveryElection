import os
import tempfile

from django.conf import settings
from django.core.management.base import BaseCommand
from organisations.models import OrganisationDivisionSet
from organisations.pmtiles_creator import PMtilesCreator

from every_election.apps.storage.s3wrapper import S3Wrapper


class Command(BaseCommand):
    help = "Run create_pmtile_for_divset for every DivisionSet."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing PMTiles if they exist.",
        )
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--all",
            action="store_true",
            help="Process all DivisionSets.",
        )
        group.add_argument(
            "--divset-ids",
            nargs="+",
            type=int,
            help="IDs of specific DivisionSets to process.",
        )

    def handle(self, *args, **options):
        self.using_s3 = False
        # Use S3 if PUBLIC_DATA_BUCKET is set
        if getattr(settings, "PUBLIC_DATA_BUCKET", None):
            self.s3_wrapper = S3Wrapper(settings.PUBLIC_DATA_BUCKET)
            self.using_s3 = True
        else:
            # Make pmtiles storage directory in static
            static_path = f"{settings.STATIC_ROOT}/pmtiles-store"
            os.makedirs(static_path, exist_ok=True)

        if self.using_s3:
            existing_pmtiles = self.s3_wrapper.list_object_keys(
                prefix="pmtiles-store/"
            )
        else:
            existing_pmtiles = os.listdir(
                f"{settings.STATIC_ROOT}/pmtiles-store/"
            )

        if options["all"]:
            qs = OrganisationDivisionSet.objects.all()
        else:
            divset_ids = set(options["divset_ids"])
            qs = OrganisationDivisionSet.objects.filter(id__in=divset_ids)
            found_ids = set(qs.values_list("id", flat=True))
            missing_ids = divset_ids - found_ids
            if missing_ids:
                warning = f"Warning: The following DivisionSet IDs do not exist: {', '.join(str(i) for i in sorted(missing_ids))}"
                self.stdout.write(self.style.WARNING(warning))

        for divset in qs:
            self.stdout.write(f"Processing DivisionSet: {divset.id}")
            # Check divset has division geographies
            if not divset.get_division_geographies().exists():
                warning = f"OrganisationDivisionSet with id '{divset.id}' has no division geographies."
                self.stdout.write(self.style.WARNING(warning))
                continue

            # Generate hash key if missing
            if not divset.pmtiles_md5_hash:
                divset.pmtiles_md5_hash = divset.generate_pmtiles_md5_hash()
                divset.save()

            if self.using_s3:
                pmtiles_fp_no_hash = (
                    f"pmtiles-store/{divset.organisation.slug}-{divset.id}"
                )
            else:
                pmtiles_fp_no_hash = f"{divset.organisation.slug}-{divset.id}"

            divset_pmtiles = self.find_existing_pmtiles_for_divset(
                existing_pmtiles, pmtiles_fp_no_hash
            )

            if divset_pmtiles:
                file_hashes = self.get_file_hashes(divset_pmtiles)
                computed_divset_hash = divset.generate_pmtiles_md5_hash()
                match = self.find_matching_hash(
                    computed_divset_hash, file_hashes
                )
                if match and not options["overwrite"]:
                    warning = f"{divset.pmtiles_file_name} already exists{' on S3' if self.using_s3 else ' locally'}. Skipping (use --overwrite to force)."
                    self.stdout.write(self.style.WARNING(warning))
                    continue
                # update hash if no matching file hash found
                divset.pmtiles_md5_hash = computed_divset_hash
                divset.save()
                # remove outdated pmtiles
                self.remove_pmtiles(divset_pmtiles)

            pmtiles_creator = PMtilesCreator(divset)

            with tempfile.TemporaryDirectory() as temp_dir:
                pmtile_fp = pmtiles_creator.create_pmtile(temp_dir)

                if self.using_s3:
                    s3_key = divset.pmtiles_s3_key
                    self.s3_wrapper.upload_file_from_fp(pmtile_fp, s3_key)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"PMTile uploaded to S3 at {s3_key}."
                        )
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

    def remove_pmtiles(self, divset_pmtiles):
        for file in divset_pmtiles:
            if self.using_s3:
                self.s3_wrapper.delete_object(file)
            else:
                os.remove(f"{settings.STATIC_ROOT}/pmtiles-store/{file}")

    def find_matching_hash(self, divset_hash, file_hashes):
        return [hash for hash in file_hashes if hash == divset_hash]

    def get_file_hashes(self, divset_pmtiles):
        file_hashes = []
        for file in divset_pmtiles:
            file_name = divset_pmtiles[0]
            file_hash = file_name.split("-")[-1].replace(".pmtiles", "")
            file_hashes.append(file_hash)

        return file_hashes

    def find_existing_pmtiles_for_divset(
        self, existing_pmtiles, pmtiles_fp_no_hash
    ):
        return [
            file
            for file in existing_pmtiles
            if file.startswith(pmtiles_fp_no_hash)
        ]
