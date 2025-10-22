import os
import tempfile
from collections import defaultdict

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
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

        existing_pmtiles_lookup = self.create_lookup_dict(existing_pmtiles)
        failures = 0

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
                failures += len(missing_ids)

        for divset in qs:
            self.stdout.write(f"Processing DivisionSet: {divset.id}")
            # Check divset has division geographies
            if not divset.get_division_geographies().exists():
                warning = f"OrganisationDivisionSet with id '{divset.id}' has no division geographies."
                self.stdout.write(self.style.WARNING(warning))
                failures += 1
                continue

            # Generate hash for current state of divset
            computed_divset_hash = divset.generate_pmtiles_md5_hash()

            fp_start = f"{divset.organisation.slug}_{divset.id}"
            existing_hashes_for_divset = existing_pmtiles_lookup[fp_start]

            if (
                computed_divset_hash in existing_hashes_for_divset
                and not options["overwrite"]
            ):
                warning = f"file with hash {computed_divset_hash} already exists for {fp_start} {' on S3' if self.using_s3 else ' locally'}. Skipping (use --overwrite to force)."
                self.stdout.write(self.style.WARNING(warning))
                continue

            # remove outdated pmtiles
            self.remove_pmtiles(fp_start, existing_hashes_for_divset)

            # Update hash on model if necessary
            if divset.pmtiles_md5_hash != computed_divset_hash:
                self.update_divset_hash(divset, computed_divset_hash)

            pmtiles_creator = PMtilesCreator(divset)

            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    pmtile_fp = pmtiles_creator.create_pmtile(temp_dir)
                except Exception as e:
                    error = f"Failed to create PMTiles for DivisionSet {divset.id}: {e}"
                    self.stdout.write(self.style.ERROR(error))
                    failures += 1
                    continue

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

        if failures:
            raise CommandError(f"Failed to process {failures} DivisionSets")

        self.stdout.write(self.style.SUCCESS("Completed successfully."))

    def update_divset_hash(self, divset, computed_divset_hash):
        divset.pmtiles_md5_hash = computed_divset_hash
        divset.save()

    def create_lookup_dict(self, existing_pmtiles):
        lookup = defaultdict(list)
        for file_path in existing_pmtiles:
            # Skip directory marker in S3 listing
            if file_path.endswith("/"):
                continue
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            file_start, file_hash = self.parse_filename(file_name)
            lookup[file_start].append(file_hash)
        return lookup

    def parse_filename(self, file_name):
        org, divset_id, file_hash = file_name.split("_")
        file_start = "_".join([org, divset_id])
        return file_start, file_hash

    def remove_pmtiles(self, fp_start, existing_hashes_for_divset):
        for file_hash in existing_hashes_for_divset:
            file_name = f"{fp_start}_{file_hash}.pmtiles"

            if self.using_s3:
                self.s3_wrapper.delete_object(f"pmtiles-store/{file_name}")
            else:
                os.remove(f"{settings.STATIC_ROOT}/pmtiles-store/{file_name}")
