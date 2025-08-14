from django.core.management import call_command
from django.core.management.base import BaseCommand
from organisations.models import OrganisationDivisionSet


class Command(BaseCommand):
    help = "Run create_pmtile_for_divset for every DivisionSet."

    def handle(self, *args, **options):
        for divset in OrganisationDivisionSet.objects.all():
            self.stdout.write(f"Processing DivisionSet: {divset.id}")
            call_command("create_pmtile_for_divset", divset.id)
        self.stdout.write(self.style.SUCCESS("All DivisionSets processed."))
