from django.core.management import BaseCommand
from elections.models import Election, MetaData


class Command(BaseCommand):
    help = """
    This command cancels a given election and any descendents.

    Example usage:
    python manage.py bulk_cancel local.essex.2025-05-01
    python manage.py bulk_cancel local.essex.2025-05-01 --metadata-id 50
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "election",
            type=str,
            help="Election to cancel. Specifying an election group or organisation group will cancel all child ballots",
        )
        parser.add_argument(
            "--metadata-id",
            action="store",
            type=int,
            help="ID of a metadata object to attach to the elections we are cancelling",
            required=False,
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
            election.cancelled = True
            if options.get("metadata_id"):
                election.metadata = MetaData.objects.get(
                    pk=options["metadata_id"]
                )
            election.save()
        self.stdout.write("..done!")
