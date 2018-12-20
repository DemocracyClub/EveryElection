"""
manage.py import_divisionsets_from_csv
  -f FILE, --file FILE  Path to import e.g: /foo/bar/baz.csv
  -u URL, --url URL     URL to import e.g: http://foo.bar/baz.csv
  -s S3, --s3 S3        S3 key to import e.g: foo/bar/baz.csv

This command imports a CSV containing division names from an Electoral
Change Order and attaches them to a new DivisionSet for each organisation.

Usually we will import from S3:
python manage.py import_divisionsets_from_csv -s "foo/bar/baz.csv"
"""


import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from organisations.models import (
    Organisation,
    OrganisationDivision,
    OrganisationDivisionSet,
)
from organisations.constants import ORG_CURIE_TO_MAPIT_AREA_TYPE, PARENT_TO_CHILD_AREAS
from core.mixins import ReadFromCSVMixin


class Command(ReadFromCSVMixin, BaseCommand):
    help = """Import from CSV at URL with the headers:
        Start Date, End Date, Name, official_identifier,
        seats_total, Boundary Commission Consultation URL, Legislation URL,
        Short Title, Notes, Mapit Generation URI, Organisation ID"""

    # dict of DivisionSet objects keyed by organisation
    # (because we can't have >1 active DivisionSets for an organisation)
    division_sets = {}
    # list of divisions
    divisions = []
    S3_BUCKET_NAME = settings.LGBCE_BUCKET

    def handle(self, *args, **options):
        self.org_curie_to_area_type = ORG_CURIE_TO_MAPIT_AREA_TYPE

        csv_data = self.load_data(options)

        # first pass over the csv builds the division sets
        self.create_division_sets(csv_data)

        # second pass over the csv builds the divisions
        self.create_divisions(csv_data)

        # now we've created all the objects,
        # save them all inside a transaction
        self.save_all()

    def get_org_from_line(self, line):
        if line["Start Date"]:
            return Organisation.objects.all().get_by_date(
                organisation_type="local-authority",
                official_identifier=line["Organisation ID"],
                date=datetime.datetime.strptime(line["Start Date"], "%Y-%m-%d").date(),
            )
        else:
            # If we haven't got a start date for the divisionset, see if we can
            # work out the org without needing one (mostly we can).
            # If we throw an exception here, we will need to call this again
            # with a start date on this divisionset
            return Organisation.objects.get(
                organisation_type="local-authority",
                official_identifier=line["Organisation ID"],
            )

    def get_start_date(self, org):
        # Given an org, work out the start date for a new division set
        # based on the end date of the most recent previous division set
        divsets = OrganisationDivisionSet.objects.filter(organisation=org)
        if not divsets:
            raise Exception(
                "Could not find any previous DivisionSets for Organisation %s" % org
            )
        if not divsets.latest().end_date:
            raise Exception(
                "End date for previous DivisionSets %s is NULL" % divsets[0]
            )
        return divsets.latest().end_date + datetime.timedelta(days=1)

    def create_division_sets(self, csv_data):
        for line in csv_data:
            org = self.get_org_from_line(line)

            if line["Start Date"]:
                # if we have specified a start date, use that
                # we might need to do this if we are importing
                # division set data for a new organisation
                start_date = line["Start Date"]
            else:
                # otherwise, infer the start date based on
                # the end date of the previous DivisionSet
                start_date = self.get_start_date(org)

            self.division_sets[org.official_identifier] = OrganisationDivisionSet(
                organisation=org,
                start_date=start_date,
                end_date=line["End Date"] or None,
                legislation_url=line["Legislation URL"],
                short_title=line["Short Title"],
                mapit_generation_id=line["Mapit Generation URI"],
                notes=line["Notes"],
                consultation_url=line["Boundary Commission Consultation URL"],
            )

    def name_to_id(self, name):
        name = name.replace("&", "and")
        name = name.strip()
        return slugify(name)

    def get_identifier_from_line(self, div_set, line):
        identifier = line["official_identifier"]
        if not identifier:
            # This area doesn't have an ID yet, so we have to create one.
            identifier = ":".join(
                [
                    div_set.organisation.official_identifier,
                    self.name_to_id(line["Name"]),
                ]
            )
        return identifier

    def get_division_type_from_registers(self, line):
        curie = ":".join([line["Organisation ID type"], line["Organisation ID"]])
        return PARENT_TO_CHILD_AREAS[self.org_curie_to_area_type[curie]][0]

    def create_div_from_line(self, org, identifier, line):

        # just in case...
        if "geography_curie" in line and line["geography_curie"]:
            raise ValueError(
                "Found content in 'geography_curie' column, but geography_curie is a virtual model field."
            )

        seats_total = line["seats_total"]
        if not seats_total:
            seats_total = 1

        div = OrganisationDivision(
            official_identifier=identifier,
            temp_id=identifier,
            organisation=org,
            name=line["Name"],
            slug=slugify(line["Name"]),
            division_type=self.get_division_type_from_registers(line),
            seats_total=seats_total,
        )
        # set a NULL placeholder for now. We'll update
        # it once the DivisionSets have been persisted
        div.divisionset = None
        return div

    def create_divisions(self, csv_data):
        for line in csv_data:
            line["Name"] = line["Name"].replace("’", "'")
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
