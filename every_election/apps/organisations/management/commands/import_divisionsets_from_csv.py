import csv

import requests

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from organisations.models import (
    Organisation,
    OrganisationDivision,
    OrganisationDivisionSet
)
from organisations.utils import add_end_date_to_previous_div_sets
from organisations.constants import (
    ORG_CURIE_TO_MAPIT_AREA_TYPE, PARENT_TO_CHILD_AREAS)


class Command(BaseCommand):
    help = """Import from CSV at URL with the headers:
        Start Date, End Date, Name, official_identifier, geography_curie,
        seats_total, Boundary Commission Consultation URL, Legislation URL,
        Short Title, Notes, Mapit Generation URI, Organisation ID"""

    def add_arguments(self, parser):
        parser.add_argument('url', action='store')

    def handle(self, *args, **options):
        self.org_curie_to_area_type = ORG_CURIE_TO_MAPIT_AREA_TYPE
        url = options['url']
        csv_reader = csv.DictReader(requests.get(url).text.splitlines())
        for line in csv_reader:
            self.add_division(line)

    def get_org_from_line(self, line):
        return Organisation.objects.get(
            official_identifier=line['Organisation ID'])

    def get_div_set(self, org, line):
        div_set, _ = OrganisationDivisionSet.objects.update_or_create(
            organisation=org,
            start_date=line['Start Date'],
            defaults={
                'end_date': line['End Date'] or None,
                'legislation_url': line['Legislation URL'],
                'short_title': line['Short Title'],
                'mapit_generation_id': line['Mapit Generation URI'],
                'notes': line['Notes'],
                'consultation_url':
                    line['Boundary Commission Consultation URL'],

            })
        add_end_date_to_previous_div_sets(div_set)
        return div_set

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
        if not getattr(self, 'register_gss_map', None):
            req = requests.get("https://raw.githubusercontent.com/openregister/local-authority-data/master/maps/gss.tsv")
            self.register_gss_map = {}
            for map_line in req.text.splitlines():
                map_line = map_line.split('\t')
                if map_line[0] == "gss":
                    continue
                self.register_gss_map[map_line[1]] = map_line[0]
                if 'principal-local-authority' in map_line[1]:
                    wls_key = map_line[1].replace(
                        'principal-local-authority',
                        'local-authority-wls',
                    )
                    self.register_gss_map[wls_key] = map_line[0]

        curie = ":".join([
            line['Organisation ID type'],
            line['Organisation ID'],
        ])
        return PARENT_TO_CHILD_AREAS[self.org_curie_to_area_type[curie]][0]

    def create_div_from_line(self, div_set, identifier, line):
        if line['geography_curie']:
            geography_curie = line['geography_curie']
        else:
            geography_curie = identifier

        seats_total = line['seats_total']
        if not seats_total:
            seats_total = 1

        div, _ = OrganisationDivision.objects.update_or_create(
            official_identifier=identifier,
            organisation=div_set.organisation,
            divisionset=div_set,
            defaults={
                'geography_curie': geography_curie,
                'name': line['Name'],
                'slug': slugify(line['Name']),
                'division_type':
                    self.get_division_type_from_registers(line),
                'seats_total': seats_total,
            }
        )
        return div

    def add_division(self, line):
        line['Name'] = line['Name'].replace("’", "'")
        org = self.get_org_from_line(line)
        div_set = self.get_div_set(org, line)
        div_identifier = self.get_identifier_from_line(div_set, line)
        self.create_div_from_line(div_set, div_identifier, line)
