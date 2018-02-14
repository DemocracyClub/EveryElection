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


from collections import namedtuple
import csv
import datetime
from io import StringIO
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from organisations.models import Organisation, OrganisationDivisionSet
from storage.s3wrapper import S3Wrapper


class Command(BaseCommand):

    ENCODING = 'utf-8'
    DELIMITER = ','
    EXPECTED_COLS = ['org', 'start_date', 'end_date']
    Record = namedtuple('Record', EXPECTED_COLS)

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            '-f',
            '--file',
            action='store',
            help='Path to import e.g: /foo/bar/baz.csv',
        )
        group.add_argument(
            '-u',
            '--url',
            action='store',
            help='URL to import e.g: http://foo.bar/baz.csv',
        )
        group.add_argument(
            '-s',
            '--s3',
            action='store',
            help='S3 key to import e.g: foo/bar/baz.csv'
        )

        parser.add_argument(
            '-o',
            '--overwrite',
            help='<Optional> Overwrite existing end dates with new values',
            action='store_true',
            required=False,
            default=False
        )

    def parse_csv(self, csv):
        header = next(csv)
        if self.EXPECTED_COLS != header:
            raise ValueError(
                "Unexpected header. Found %s expected %s" %\
                (str(header), str(self.EXPECTED_COLS))
            )
        return [self.Record(*row) for row in csv]

    def read_local_csv(self, filename):
        f = open(filename, 'rt', encoding=self.ENCODING)
        reader = csv.reader(f, delimiter=self.DELIMITER)
        return reader

    def read_csv_from_url(self, url):
        r = requests.get(url)
        r.raise_for_status()
        reader = csv.reader(StringIO(r.text), delimiter=self.DELIMITER)
        return reader

    def read_csv_from_s3(self, filepath):
        s3 = S3Wrapper(settings.LGBCE_BUCKET)
        f = s3.get_file(filepath)
        return self.read_local_csv(f.name)

    def prepare_data(self, data):
        # validate and enrich input data
        return [self.Record(
            Organisation.objects.get(official_identifier=rec.org),
            datetime.datetime.strptime(rec.start_date, "%Y-%m-%d").date(),
            datetime.datetime.strptime(rec.end_date, "%Y-%m-%d").date()
        ) for rec in data]

    def handle(self, **options):
        if options['file']:
            data = self.parse_csv(self.read_local_csv(options['file']))
        if options['url']:
            data = self.parse_csv(self.read_csv_from_url(options['url']))
        if options['s3']:
            data = self.parse_csv(self.read_csv_from_s3(options['s3']))
        data = self.prepare_data(data)

        updates = []
        for rec in data:
            ods = OrganisationDivisionSet.objects.get(
                organisation=rec.org,
                start_date=rec.start_date
            )
            if ods.end_date and not options['overwrite']:
                self.stdout.write(
                    'Record %s already has an end date. To overwrite it, '
                    're-run the command with the --overwrite flag.' % (str(ods)))
            else:
                ods.end_date = rec.end_date
                updates.append(ods)

        """
        only persist anything to the DB if we made it this far
        i.e: if anything thew OrganisationDivisionSet.DoesNotExist
        we won't write any changes to the DB
        """
        for rec in updates:
            self.stdout.write('Updating end_date for %s' % (str(rec)))
            rec.save()
