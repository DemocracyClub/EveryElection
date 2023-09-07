from dateutil.parser import parse
from django.core.management.base import BaseCommand
from django.db import transaction
from elections.sync_helper import ElectionSyncer


class Command(BaseCommand):
    def valid_date(self, value):
        return parse(value)

    def add_arguments(self, parser):
        parser.add_argument(
            "--since",
            action="store",
            dest="since",
            type=self.valid_date,
            help="Import changes since [datetime]",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.syncer = ElectionSyncer(since=options["since"])
