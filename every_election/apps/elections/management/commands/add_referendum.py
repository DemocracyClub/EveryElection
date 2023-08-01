from django.core.management import BaseCommand
from elections.models import (
    Election,
    ElectionType,
    ModerationHistory,
    ModerationStatuses,
)
from organisations.models import Organisation


class Command(BaseCommand):
    help = """
    Adds an election with an election type of referendum
    Example usage:
    python manage.py add_referendum --date 2021-10-07 \
        --council croydon \
        --election-title "Governance referendum" \
        --official-identifier CRY \
        --org-type local-authority
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-d",
            "--date",
            action="store",
            dest="date",
            help="The date the referendum is taking place",
            required=True,
        )
        parser.add_argument(
            "-c",
            "--council",
            action="store",
            dest="council",
            help="The council area the referendum is taking place",
            required=True,
        )
        parser.add_argument(
            "-t",
            "--election-title",
            action="store",
            dest="election_title",
            help="The election title to be used",
            required=True,
        )
        parser.add_argument(
            "--official-identifier",
            action="store",
            dest="official_identifier",
            help="The official identifier for the related Organisation. Election will cover the whole organisation unless a division ID is passed",
            required=True,
        )
        parser.add_argument(
            "--org-type",
            action="store",
            dest="org_type",
            help="The council area the referendum is taking place",
            required=True,
        )
        parser.add_argument(
            "--division-id",
            action="store",
            dest="division_id",
            help="ID of a OrganisationDivision if applicable",
            required=False,
        )

    def handle(self, *args, **options):
        election_date = options["date"]
        election_id = f"ref.{options['council']}.{election_date}"

        referendum_type = ElectionType.objects.get(election_type="ref")

        group_election, created = Election.private_objects.update_or_create(
            election_id=f"ref.{election_date}",
            defaults={
                "election_type": referendum_type,
                "poll_open_date": election_date,
                "election_title": "Referendum elections",
                "current": True,
                "division_id": options["division_id"],
                "group_type": "election",
            },
        )

        ref_election, created = Election.private_objects.update_or_create(
            election_id=election_id,
            defaults={
                "election_type": referendum_type,
                "poll_open_date": election_date,
                "election_title": options["election_title"],
                "current": True,
                "division_id": options["division_id"],
                "voting_system": "FPTP",
                "group": group_election,
            },
        )

        self.stdout.write(
            f"{'Created' if created else 'Updated'} {election_id}"
        )

        ModerationHistory.objects.get_or_create(
            status_id=ModerationStatuses.approved.value,
            election=group_election,
        )

        ModerationHistory.objects.get_or_create(
            status_id=ModerationStatuses.approved.value,
            election=ref_election,
        )

        org = Organisation.objects.get_by_date(
            date=election_date,
            official_identifier=options["official_identifier"],
            organisation_type=options["org_type"],
        )
        ref_election.organisation = org
        ref_election.organisation_geography = org.geographies.latest()
        if ref_election.division:
            ref_election.division_geography = ref_election.division.geography

        ref_election.save()
