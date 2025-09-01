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
        failures = 0
        for divset in OrganisationDivisionSet.objects.all():
            self.stdout.write(f"Processing DivisionSet: {divset.id}")
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
