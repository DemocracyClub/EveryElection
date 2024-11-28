from django.core.management import BaseCommand
from elections.models import Election
from elections.utils import get_voter_id_requirement


class Command(BaseCommand):
    help = """
    This command refreshes the requires_voter_id property on a given election
    and any descendents. Use this command if we've just updated the
    uk-election-ids library with new ID requirements which affect elections we
    have already created in EE.

    Example usage:
    python manage.py refresh_voter_id local.city-of-london.2025-03-20
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "election",
            type=str,
            help="Election to update. Specifying an election group or organisation group will refresh all child ballots",
        )

    def handle(self, *args, **options):
        election_id = options["election"]
        elections = (
            Election.public_objects.get(election_id=election_id)
            .get_descendents("public_objects", inclusive=True)
            .order_by("election_id")
        )
        self.stdout.write(f"updating {elections.count()} elections..")
        for election in elections:
            self.stdout.write(f"updating {election.election_id}..")
            election.requires_voter_id = get_voter_id_requirement(election)
            election.save()
        self.stdout.write("..done!")
