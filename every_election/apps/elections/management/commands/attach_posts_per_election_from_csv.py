from django.core.management.base import BaseCommand
from django.db import transaction

from core.mixins import ReadFromCSVMixin
from elections.models import Election


class Command(ReadFromCSVMixin, BaseCommand):

    SEATS_CONTESTED_FIELD = 'posts up'

    help = """
    Given a CSV file, path or url import the number of contested seats for that
    election.

    Expected CSV format is, e.g:

    ORG Name,ORG GSS,REG,geography_curie,ward name,seats_total,has_election,posts up,created,id,problem/note
    Eastleigh,E07000086,EAT,EAT:bishopstoke,Bishopstoke,3,yes,3,yes,local.eastleigh.bishopstoke.2018-05-03,
    Eastleigh,E07000086,EAT,EAT:botley,Botley,2,yes,2,yes,local.eastleigh.botley.2018-05-03,


    Optionally update the seats total for that election if
    --replace-seats-total specified.
    """  # noqa

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--replace-seats-total',
            action='store_true',
            help="Replace seats total in the database with the value in the CSV file"  # noqa
        )
        parser.add_argument(
            '--skip-unknown',
            action='store_true',
            help="Skip elections with unknown seats total"
        )

    def get_seats_total(self, election, line, trust_csv=False):
        csv_seats_total = None
        db_seats_total = None
        seats_total = None

        # See if we already have the seats_total
        if election.division.seats_total:
            db_seats_total = election.division.seats_total

        if line['seats_total']:
            csv_seats_total = int(line['seats_total'] or None)

        if db_seats_total:
            # Warn if the CSV has a different seats total
            if csv_seats_total != db_seats_total:
                self.stdout.write(
                    "Seats total mismatch for {} ({} vs {})".format(
                        election.election_id,
                        csv_seats_total,
                        db_seats_total,
                    ))
            seats_total = db_seats_total
        else:
            if trust_csv and csv_seats_total and csv_seats_total > 0:
                self.stdout.write("Taking seats total from CSV for {}".format(
                    election.election_id,
                ))
                seats_total = csv_seats_total

        return seats_total

    def get_seats_contested(self, line):
        try:
            seats_contested = int(line[self.SEATS_CONTESTED_FIELD] or 0)
        except ValueError:
            raise ValueError(
                "Seats contested must be int. Found {}".format(
                    type(line[self.SEATS_CONTESTED_FIELD])
                ))
        return seats_contested

    @transaction.atomic
    def save_all(self, updated_elections):
        for election in updated_elections:
            election.save()

    def handle(self, *args, **options):
        data = self.load_data(options)
        trust_csv = options['replace_seats_total']
        updated_elections = []
        for line in data:
            if line['created'] == "yes":

                election = Election.public_objects.get(
                    election_id=line['id']
                )
                seats_contested = self.get_seats_contested(line)

                seats_total = self.get_seats_total(
                    election,
                    line,
                    trust_csv=trust_csv,
                )
                if seats_total is None:
                    message = "Seats total not known for {}".format(
                            election.election_id
                        )
                    if options['skip_unknown']:
                        self.stdout.write(message)
                    else:
                        raise ValueError(message)

                if seats_total and not seats_total >= seats_contested:
                    raise ValueError(
                        "seats total less than seats_contested for {}".format(
                            election.election_id))

                election.seats_contested = seats_contested
                if seats_total and trust_csv:
                    election.seats_total = seats_total
                updated_elections.append(election)

        self.save_all(updated_elections)
