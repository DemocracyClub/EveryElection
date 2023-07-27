"""
manage.py update_end_dates
  -f FILE, --file FILE  Path to import e.g: /foo/bar/baz.csv
  -u URL, --url URL     URL to import e.g: http://foo.bar/baz.csv
  -s S3, --s3 S3        S3 key to import e.g: foo/bar/baz.csv
  -o, --overwrite       <Optional> Overwrite existing end dates with new values

This command imports a CSV file of the form

org,start_date,end_date
AAA,2017-01-01,2017-12-31
BBB,2017-01-01,2017-12-31

and updates OrganisationDivisionSet end_date if NULL
(or even if they aren't NULL when using the --overwrite flag)

Usually we will import from S3:
python manage.py update_end_dates -s "foo/bar/baz.csv"
"""


import datetime
from collections import namedtuple

from core.mixins import ReadFromCSVMixin
from django.conf import settings
from django.core.management.base import BaseCommand
from organisations.models import Organisation, OrganisationDivisionSet


class Command(ReadFromCSVMixin, BaseCommand):
    EXPECTED_COLS = ["org", "start_date", "end_date"]
    Record = namedtuple("Record", EXPECTED_COLS)
    S3_BUCKET_NAME = settings.LGBCE_BUCKET

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "-o",
            "--overwrite",
            help="<Optional> Overwrite existing end dates with new values",
            action="store_true",
            required=False,
            default=False,
        )

    def validate_csv(self, csv):
        header = list(csv[0].keys())
        if sorted(header) != sorted(self.EXPECTED_COLS):
            raise ValueError(
                "Unexpected header. Found {} expected {}".format(
                    str(header), str(self.EXPECTED_COLS)
                )
            )

    def prepare_data(self, data):
        # validate and enrich input data

        ret = []
        for rec in data:
            divset_start_date = datetime.datetime.strptime(
                rec["start_date"], "%Y-%m-%d"
            ).date()
            divset_end_date = datetime.datetime.strptime(
                rec["end_date"], "%Y-%m-%d"
            ).date()
            org = Organisation.objects.all().get_by_date(
                organisation_type="local-authority",
                official_identifier=rec["org"],
                date=divset_start_date,
            )
            if org.end_date and divset_end_date > org.end_date:
                raise ValueError(
                    "Organisation end_date is %s but supplied "
                    "end_date for DivisionSet is %s. DivisionSet end date "
                    "must be on or before %s."
                    % (
                        org.end_date.isoformat(),
                        divset_end_date.isoformat(),
                        org.end_date.isoformat(),
                    )
                )
            ret.append(self.Record(org, divset_start_date, divset_end_date))
        return ret

    def handle(self, **options):
        data = self.load_data(options)
        self.validate_csv(data)
        data = self.prepare_data(data)

        updates = []
        for rec in data:
            ods = OrganisationDivisionSet.objects.get(
                organisation=rec.org, start_date=rec.start_date
            )
            if ods.end_date and not options["overwrite"]:
                self.stdout.write(
                    "Record %s already has an end date. To overwrite it, "
                    "re-run the command with the --overwrite flag." % (str(ods))
                )
            else:
                ods.end_date = rec.end_date
                updates.append(ods)

        """
        only persist anything to the DB if we made it this far
        i.e: if anything thew OrganisationDivisionSet.DoesNotExist
        we won't write any changes to the DB
        """
        for rec in updates:
            self.stdout.write("Updating end_date for %s" % (str(rec)))
            rec.save()
