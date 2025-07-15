from core.mixins import ReadFromCSVMixin
from django.core.management import BaseCommand
from django.db import transaction
from elections.models import Election


class Command(ReadFromCSVMixin, BaseCommand):
    help = """
    one-off command to set the correct seats contested and total seats for historic elections.

    update_historic_seats_values_from_csv -u "https://docs.google.com/spreadsheets/d/e/2PACX-1vSXaZ20SSUmtN65_wqz8Zytu71h8MPBnDEwtCovfxRQASkSl2izgmWV1hceUgW8oSp5nKApw67PFeGI/pub?gid=1508742918&single=true&output=csv"
    update_historic_seats_values_from_csv -f path/to/local/file.csv
    """

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run the command without making any changes to the database.",
        )

    def handle(self, *args, **options):
        data = self.load_data(options)
        records_to_update = []

        for line in data:
            # skip referendums and gla.a.
            if line["election_id"].startswith(("ref.", "gla.a.")):
                continue
            record = Election.public_objects.get(
                election_id=line["election_id"]
            )
            # update parl, mayor, pcc
            if record.election_id.startswith(("parl.", "mayor.", "pcc.")):
                if not record.seats_contested:
                    record.seats_contested = 1
                record.seats_total = 1
                records_to_update.append(record)
                continue

            updated = False
            if line["division_seats_total"].isdigit():
                record.seats_total = int(line["division_seats_total"])
                updated = True
            if line["ynr_seats_contested"].isdigit():
                record.seats_contested = int(line["ynr_seats_contested"])
                updated = True
            if updated:
                records_to_update.append(record)

        if options["dry_run"]:
            self.stdout.write(
                f"Dry run: would update {len(records_to_update)} records."
            )
        else:
            self.save_records(records_to_update)

    @transaction.atomic()
    def save_records(self, records):
        Election.public_objects.bulk_update(
            records, ["seats_total", "seats_contested"]
        )
        self.stdout.write(f"Updated {len(records)} records.")
