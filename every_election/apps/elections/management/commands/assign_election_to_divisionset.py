"""
This management command assigns elections from election groups to a given divisionset's divisions.

This is usually used when we're processing Community Governance Reviews as decscribed in this issue:

https://github.com/DemocracyClub/EveryElection/issues/570.

python manage.py assign_election_to_divisionset <election_ids> <divisionset_id>

example:
python manage.py assign_election_to_divisionset local.broxtowe.2023-05-04 local.broxtowe.2024-05-02 794
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from elections.models import Election
from organisations.models import OrganisationDivision


class Command(BaseCommand):
    help = "Tries to assign elections from election groups to a given divisionset's divisions"

    def add_arguments(self, parser):
        parser.add_argument(
            "election_group_ids",
            action="store",
            nargs="+",
            help="space separated list of election_ids",
        )
        parser.add_argument(
            "divset_id",
            action="store",
            type=int,
            help="The divisionset_id of the divisionset",
        )

    def handle(self, *args, **options):
        divset_id = options["divset_id"]
        election_group_ids = options["election_group_ids"]

        elections = self.get_elections(election_group_ids)

        self.assign_elections_to_divisionset(divset_id, elections)

    def assign_elections_to_divisionset(self, divset_id, elections):
        # Find election division in the new divisionset and update the election
        for e in elections:
            try:
                new_div = OrganisationDivision.objects.get(
                    divisionset_id=divset_id,
                    official_identifier=e.division.official_identifier,
                )
                e.division = new_div
                e.division_geography = new_div.geography
                self.stdout.write(
                    f"Assigned {e.election_id} to "
                    f"{new_div.name} ({new_div.official_identifier}) from divisionset {divset_id}"
                )
            except OrganisationDivision.DoesNotExist:
                raise CommandError(
                    f"Division with official_identifier {e.division.official_identifier} not found in divisionset {divset_id}."
                )
        self.stdout.write("Saving...")
        # Save all elections in a single transaction
        with transaction.atomic():
            for e in elections:
                e.save()
        self.stdout.write("...Done")

    def get_elections(self, election_group_ids):
        election_groups = Election.public_objects.all().filter(
            election_id__in=election_group_ids
        )

        if len(election_group_ids) != election_groups.count():
            raise CommandError(
                f"Expected {len(election_group_ids)} election groups with ids {election_group_ids} but found {election_groups.count()}"
            )

        elections = []
        for eg in election_groups:
            elections.extend(eg.get_children("public_objects").all())
        return elections
