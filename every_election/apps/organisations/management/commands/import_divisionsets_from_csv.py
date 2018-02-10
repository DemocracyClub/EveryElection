import csv
import re
import requests
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from organisations.models import (
    Organisation,
    OrganisationDivision,
    OrganisationDivisionSet
)
from organisations.constants import (
    ORG_CURIE_TO_MAPIT_AREA_TYPE, PARENT_TO_CHILD_AREAS)
from storage.s3wrapper import S3Wrapper


class Command(BaseCommand):
    help = """Import from CSV at URL with the headers:
        Start Date, End Date, Name, official_identifier, geography_curie,
        seats_total, Boundary Commission Consultation URL, Legislation URL,
        Short Title, Notes, Mapit Generation URI, Organisation ID"""

    # dict of DivisionSet objects keyed by organisation
    # (because we can't have >1 active DivisionSets for an organisation)
    division_sets = {}
    # list of divisions
    divisions = []
    ENCODING = 'utf-8'
    DELIMITER = ','

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

    def handle(self, *args, **options):
        self.org_curie_to_area_type = ORG_CURIE_TO_MAPIT_AREA_TYPE

        if options['file']:
            csv_data = self.read_local_csv(options['file'])
        if options['url']:
            csv_data = self.read_csv_from_url(options['url'])
        if options['s3']:
            csv_data = self.read_csv_from_s3(options['s3'])

        # first pass over the csv builds the division sets
        self.create_division_sets(csv_data)

        # second pass over the csv builds the divisions
        self.create_divisions(csv_data)

        # now we've created all the objects,
        # save them all inside a transaction
        self.save_all()

    def read_local_csv(self, filename):
        f = open(filename, 'rt', encoding=self.ENCODING)
        reader = csv.DictReader(f, delimiter=self.DELIMITER)
        return list(reader)

    def read_csv_from_url(self, url):
        r = requests.get(url)

        # if CSV came from google docs
        # manually set the encoding
        gdocs_pattern = r'(.)+docs\.google(.)+\/ccc(.)+'
        if re.match(gdocs_pattern, url):
            r.encoding = self.ENCODING

        csv_reader = csv.DictReader(r.text.splitlines())
        return list(csv_reader)

    def read_csv_from_s3(self, filepath):
        s3 = S3Wrapper(settings.LGBCE_BUCKET)
        f = s3.get_file(filepath)
        return self.read_local_csv(f.name)

    def get_org_from_line(self, line):
        return Organisation.objects.get(
            official_identifier=line['Organisation ID'])

    def get_start_date(self, org):
        # Given an org, work out the start date for a new division set
        # based on the end date of the most recent previous division set
        divsets = OrganisationDivisionSet.objects.filter(organisation=org)
        if not divsets:
            raise Exception('Could not find any previous DivisionSets for Organisation %s' % org)
        if not divsets.latest().end_date:
            raise Exception('End date for previous DivisionSets %s is NULL' % divsets[0])
        return divsets.latest().end_date + timedelta(days=1)

    def create_division_sets(self, csv_data):
        for line in csv_data:
            org = self.get_org_from_line(line)

            if line['Start Date']:
                # if we have specified a start date, use that
                # we might need to do this if we are importing
                # division set data for a new organisation
                start_date = line['Start Date']
            else:
                # otherwise, infer the start date based on
                # the end date of the previous DivisionSet
                start_date = self.get_start_date(org)

            self.division_sets[org.official_identifier] = OrganisationDivisionSet(
                organisation=org,
                start_date=start_date,
                end_date=line['End Date'] or None,
                legislation_url=line['Legislation URL'],
                short_title=line['Short Title'],
                mapit_generation_id=line['Mapit Generation URI'],
                notes=line['Notes'],
                consultation_url=line['Boundary Commission Consultation URL']
            )

    def name_to_id(self, name):
        name = name.replace("&", "and")
        name = name.strip()
        return slugify(name)

    def get_identifier_from_line(self, div_set, line):
        identifier = line['official_identifier']
        if not identifier:
            # This area doesn't have an ID yet, so we have to create one.
            identifier = ":".join([
                div_set.organisation.official_identifier,
                self.name_to_id(line['Name'])
            ])
        return identifier

    def get_division_type_from_registers(self, line):
        curie = ":".join([
            line['Organisation ID type'],
            line['Organisation ID'],
        ])
        return PARENT_TO_CHILD_AREAS[self.org_curie_to_area_type[curie]][0]

    def create_div_from_line(self, org, identifier, line):
        if line['geography_curie']:
            geography_curie = line['geography_curie']
        else:
            geography_curie = identifier

        seats_total = line['seats_total']
        if not seats_total:
            seats_total = 1

        div = OrganisationDivision(
            official_identifier=identifier,
            organisation=org,
            geography_curie=geography_curie,
            name=line['Name'],
            slug=slugify(line['Name']),
            division_type=self.get_division_type_from_registers(line),
            seats_total=seats_total,
        )
        # set a NULL placeholder for now. We'll update
        # it once the DivisionSets have been persisted
        div.divisionset = None
        return div

    def create_divisions(self, csv_data):
        for line in csv_data:
            line['Name'] = line['Name'].replace("’", "'")
            org = self.get_org_from_line(line)
            div_set = self.division_sets[org.official_identifier]
            div_identifier = self.get_identifier_from_line(div_set, line)
            division = self.create_div_from_line(org, div_identifier, line)
            self.divisions.append(division)

    @transaction.atomic
    def save_all(self):
        for _, record in self.division_sets.items():
            record.save()
        for record in self.divisions:
            org = self.division_sets[record.organisation.official_identifier]
            record.divisionset = org
            record.save()
