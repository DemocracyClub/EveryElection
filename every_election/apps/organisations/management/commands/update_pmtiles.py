import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from organisations.models import OrganisationDivisionSet


class Command(BaseCommand):
    help = "Run create_pmtile_for_divset for every DivisionSet."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing PMTiles if they exist.",
        )

    def handle(self, *args, **options):
        existing_pmtiles = os.listdir(f"{settings.STATIC_ROOT}/pmtiles-store/")

        failures = 0
        for divset in OrganisationDivisionSet.objects.all():
            self.stdout.write(f"Processing DivisionSet: {divset.id}")
            # Generate hash key if missing
            if not divset.pmtiles_md5_hash:
                divset.pmtiles_md5_hash = divset.generate_pmtiles_md5_hash()
                divset.save()

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
                    continue
                # update hash if no matching file hash found
                divset.pmtiles_md5_hash = computed_divset_hash
                divset.save()
                # remove outdated pmtiles
                self.remove_pmtiles(divset_pmtiles)

            try:
                call_command(
                    "create_pmtiles_for_divset",
                    divset.id,
                    overwrite=options["overwrite"],
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error processing DivisionSet ID {divset.id}: {str(e)}"
                    )
                )
                failures += 1
        if failures == 0:
            self.stdout.write(
                self.style.SUCCESS("All DivisionSets processed successfully.")
            )
        else:
            raise CommandError(f"Failed to process {failures} DivisionSets")

    def remove_pmtiles(self, divset_pmtiles):
        for file in divset_pmtiles:
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
