import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from organisations.models import (
    Organisation,
    OrganisationDivision,
    OrganisationDivisionSet
)

from core.mixins import ReadFromCSVMixin


class Command(ReadFromCSVMixin, BaseCommand):
    """
    Bespoke import command for importing NI District Electoral Areas
    from a custom CSV assembled from
    http://www.legislation.gov.uk/uksi/2014/270/made
    https://github.com/mysociety/mapit/blob/master/mapit_gb/data/ni-electoral-areas-2015.csv
    https://www.registers.service.gov.uk/registers/statistical-geography-local-government-district-nir
    """

    division_sets = {}
    divisions = []
    start_date = '2014-05-22'

    def handle(self, *args, **options):
        csv_data = self.load_data(options)

        # first pass over the csv builds the division sets
        self.create_division_sets(csv_data)

        # second pass over the csv builds the divisions
        self.create_divisions(csv_data)

        # now we've created all the objects,
        # save them all inside a transaction
        self.save_all()

    def get_org_from_line(self, line):
        return Organisation.objects.all().get_by_date(
            organisation_type='local-authority',
            official_identifier=line['District Register Code'],
            date=datetime.datetime.strptime('2015-04-01', "%Y-%m-%d").date()
        )

    def create_division_sets(self, csv_data):
        for line in csv_data:
            org = self.get_org_from_line(line)
            self.division_sets[org.official_identifier] = OrganisationDivisionSet(
                organisation=org,
                start_date=self.start_date,
                end_date=None,
                legislation_url='http://www.legislation.gov.uk/uksi/2014/270/made',
                short_title='The District Electoral Areas (Northern Ireland) Order 2014',
                mapit_generation_id='',
                notes='',
                consultation_url=''
            )

    def create_divisions(self, csv_data):
        for line in csv_data:
            org = self.get_org_from_line(line)
            id_ = "gss:{}".format(line['District Electoral Area GSS code'])
            div = OrganisationDivision(
                official_identifier=id_,
                temp_id='',
                organisation=org,
                name=line['District Electoral Area'],
                slug=slugify(line['District Electoral Area']),
                division_type='LGE',
                seats_total=line['Number of councillors'],
            )
            # set a NULL placeholder for now. We'll update
            # it once the DivisionSets have been persisted
            div.divisionset = None

            self.divisions.append(div)

    @transaction.atomic
    def save_all(self):
        for _, record in self.division_sets.items():
            record.save()
        for record in self.divisions:
            org = self.division_sets[record.organisation.official_identifier]
            record.divisionset = org
            record.save()
