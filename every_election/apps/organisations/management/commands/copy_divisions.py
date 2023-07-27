from django.core.management.base import BaseCommand
from django.db import transaction
from organisations.models import OrganisationDivision, OrganisationDivisionSet


class Command(BaseCommand):
    help = "Copy all of the division and geography objects from one DivisionSet to another"

    def add_arguments(self, parser):
        parser.add_argument(
            "src_id", action="store", help="PK for the source DivisionSet"
        )
        parser.add_argument(
            "dst_id", action="store", help="PK for the destination DivisionSet"
        )

    @transaction.atomic
    def copy_divsions(self, old_divset_id, new_divset_id):
        try:
            old_divset = OrganisationDivisionSet.objects.get(pk=old_divset_id)
        except OrganisationDivisionSet.DoesNotExist:
            raise Exception("Invalid Source DivisionSet")
        try:
            new_divset = OrganisationDivisionSet.objects.get(pk=new_divset_id)
        except OrganisationDivisionSet.DoesNotExist:
            raise Exception("Invalid Destination DivisionSet")

        if len(new_divset.divisions.all()) > 0:
            raise Exception("Target DivisionSet must be empty")

        self.stdout.write(
            f"Copying all divisions from {str(old_divset)} to {str(new_divset)}..."
        )

        # copy the divisions
        for div in old_divset.divisions.all():
            div.pk = None
            div.divisionset = new_divset
            div.save()

        # copy the geographies
        geographies = [
            (div.official_identifier, div.geography)
            for div in old_divset.divisions.all()
        ]
        for gss, geog in geographies:
            div = OrganisationDivision.objects.get(
                official_identifier=gss, divisionset=new_divset
            )

            geog.pk = None
            geog.division_id = div.id
            geog.save()
            # attach it to the target division
            div.geography = geog
            div.save()

        assert len(old_divset.divisions.all()) == len(
            new_divset.divisions.all()
        )

        self.stdout.write("...done!")

    def handle(self, *args, **options):
        self.copy_divsions(options["src_id"], options["dst_id"])
