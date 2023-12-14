import io

from dateutil.parser import parse
from django.core.management.base import BaseCommand, OutputWrapper
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
        parser.add_argument(
            "--raise-errors",
            action="store_true",
            help="Raises exception for import errors, for later logging",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        stderr = self.stderr
        if options["raise_errors"]:
            # Add a String IO that can capture all the errors
            stderr = OutputWrapper(io.StringIO())
        syncer = ElectionSyncer(
            since=options["since"], stdout=self.stdout, stderr=stderr
        )
        syncer.run_import()

        if options["raise_errors"]:
            stderr._out.seek(0)
            errors = "\t".join(stderr._out.readlines())
            if errors:
                raise ValueError(f"Error importing some ballots: \n\t{errors}")
