from django.core.management.base import BaseCommand

from core.mixins import ReadFromCSVMixin
from organisations.models import OrganisationDivisionSet, OrganisationDivision


class Command(ReadFromCSVMixin, BaseCommand):
    help = """Takes a CSV in the format name,seats_total and updates the 
    seats_total for matching divisions"""

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--divisionset",
            action="store",
            help="PK for the DivisionSet to update",
            required=True,
        )
        parser.add_argument(
            "--override",
            action="store_true",
            help="Override existing values in seats_total",
        )

    def handle(self, *args, **options):
        division_set = OrganisationDivisionSet.objects.get(
            pk=options["divisionset"]
        )
        csv_data = self.load_data(options)

        division_names = set(
            division_set.divisions.values_list("name", flat=True)
        )
        csv_names = set([r["name"] for r in csv_data])
        if division_names != csv_names:
            self.stderr.write("Name mismatch")
            self.stderr.write("==============")
            self.stderr.write("Names in database not in CSV")
            self.stderr.write("\t" + "\n\t".join(division_names - csv_names))

            self.stderr.write("Names in CSV not in database")
            self.stderr.write("\t" + "\n\t".join(csv_names - division_names))

        for line in csv_data:
            division: OrganisationDivision = division_set.divisions.get(
                name=line["name"]
            )
            if division.seats_total and not options["override"]:
                self.stdout.write(
                    "Skipping division with existing "
                    "seats_total: {} ({})".format(division.name, division.pk)
                )
                continue

            division.seats_total = line["seats_total"]
            division.save()
            self.stdout.write(
                "Set seats_total to {} for {} ({})".format(
                    division.seats_total, division.name, division.pk
                )
            )
