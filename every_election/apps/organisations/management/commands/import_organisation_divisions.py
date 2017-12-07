from datetime import datetime, timedelta

import requests
import requests_cache

requests_cache.install_cache('demo_cache')
CACHE = requests_cache.get_cache()

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from organisations.models import (
    Organisation,
    OrganisationDivision,
    OrganisationDivisionSet
)
from organisations.constants import PARENT_TO_CHILD_AREAS


class Command(BaseCommand):
    skip_gss = [
        "E12000007",
        "W08000001"  # See import_welsh_areas
    ]
    BASE = "http://mapit.mysociety.org"

    def add_arguments(self, parser):
        parser.add_argument(
            '--always_pick_option', action='store', type=int, default=0)

    def handle(self, **options):
        self.always_pick_option = int(options['always_pick_option'])
        self.load_mapit_generations()

        self.import_scottish_areas()
        self.import_gla_areas()
        self.import_parl_areas()
        self.import_ni_areas()
        self.import_welsh_areas()

        qs = Organisation.objects.exclude(gss='')
        qs = qs.exclude(gss=None)
        qs = qs.exclude(gss__startswith='N')
        qs = qs.exclude(gss__in=self.skip_gss)
        self.process_qs(qs)

    def process_qs(self, qs, default_child_types=None):
        for organisation in qs:
            initial_url = "{}/area/{}".format(self.BASE, organisation.gss)
            req = requests.get(initial_url)
            url = req.url

            url = "{}/children".format(url)
            if not default_child_types:
                parent_type = req.json()['type']
                child_types = PARENT_TO_CHILD_AREAS.get(parent_type)
                if child_types:
                    child_types = ",".join(child_types)
                    url = "{}?type={}".format(url, child_types)
            req = requests.get(url)
            self.import_divisions(organisation, req.json())

    def load_mapit_generations(self):
        url = "{}/generations".format(self.BASE)
        self.mapit_generations = requests.get(url).json()
        for generation_id, generation in self.mapit_generations.items():
            generation['uri'] = "{}/{}".format(url, generation_id)

    def create_single_division(self, division_set,
                               organisation, mapit_dict,
                               division_election_sub_type=''):
        all_codes = [
            ('gss', mapit_dict['codes'].get('gss')),
            ('ons', mapit_dict['codes'].get('ons')),
            ('unit_id', mapit_dict['codes'].get('unit_id')),
            ('osni_oid', mapit_dict['codes'].get('osni_oid')),
        ]
        all_codes = [
            (code_type, code_value)
            for code_type, code_value in all_codes
            if code_value
        ]

        geography_curie = ":".join(all_codes[0])

        territory_code = ""
        if geography_curie.startswith('gss:E'):
            territory_code = "ENG"
        if geography_curie.startswith('gss:W'):
            territory_code = "WLS"
        if geography_curie.startswith('gss:S'):
            territory_code = "SCT"
        if geography_curie.startswith('gss:N'):
            territory_code = "NIR"
        if geography_curie.startswith('osni_oid'):
            territory_code = "NIR"

        OrganisationDivision.objects.update_or_create(
            official_identifier=geography_curie,
            organisation=organisation,
            divisionset=division_set,
            defaults={
                'geography_curie': geography_curie,
                'name': mapit_dict['name'],
                'slug': slugify(mapit_dict['name']),
                'division_type': mapit_dict['type'],
                'division_subtype': mapit_dict['type_name'],
                'mapit_generation_low': int(mapit_dict['generation_low']),
                'mapit_generation_high': int(mapit_dict['generation_high']),
                'territory_code': territory_code,
                'division_election_sub_type': division_election_sub_type,
            }
        )

    def _create_division_set(self, organisation, mapit_generation_uri,
                             mapit_generation_start_date):
        print("Creating")
        print(organisation)
        print("Creating")
        division_set, _ = OrganisationDivisionSet.objects.update_or_create(
            organisation=organisation,
            mapit_generation_id=mapit_generation_uri,
            defaults={
                'start_date': mapit_generation_start_date,
                'short_title': "{} Boundaries".format(
                    mapit_generation_start_date[:4]),
                'notes': "Auto imported from {}".format(self.BASE),
            }
        )
        return division_set

    def get_division_set(self, organisation, division):
        mapit_generation = self.mapit_generations.get(
            str(division['generation_low'])
        )
        mapit_generation_uri = mapit_generation['uri']
        mapit_generation_start_date = mapit_generation['created'].split('T')[0]


        try:
            division_set = OrganisationDivisionSet.objects.get(
                mapit_generation_id=mapit_generation_uri,
                organisation=organisation
            )
        except OrganisationDivisionSet.DoesNotExist:
            # We've not recoreded that we know about this OrganisationDivisionSet yet so we…
            # 1 Figure out if it's because it's a new one from MapIt or not
            existing_division_sets = OrganisationDivisionSet.objects.filter(
                organisation=organisation,
                start_date__lte=mapit_generation_start_date
            )
            if not existing_division_sets:
                # There are no sets before this mapit set, so we assume it's
                # just brand new to us (first import, or we've not manually
                # created one)
                division_set = self._create_division_set(
                    organisation,
                    mapit_generation_uri, mapit_generation_start_date
                    )
            else:
                ds = existing_division_sets.first()
                print("This might be a new OrganisationDivisionSet…")
                print('Found a MaPit generation "{}" ("{}") dated {}'.format(
                    mapit_generation_uri,
                    mapit_generation['description'],
                    mapit_generation_start_date,
                ))
                msg = " ".join([
                "We know about an existing division set starting on {} ",
                """with the title "{}" and note "{}". """,
                """\nThere are 2 options:""",
                """\n 1. Assert that the existing set is part of this""",
                """MaPit generation""",
                """\n 2. Make a new generation, and set the end date of""",
                """the new generation to the day before the start date""",
                """of the new one""",
                """\n\nIf you're not sure you should quit this script and""",
                """figure it out another way""",
                ])
                msg = msg.format(
                        ds.start_date,
                        ds.short_title,
                        ds.notes,
                    )
                print(msg)
                if self.always_pick_option in [1,2]:
                    decision = self.always_pick_option
                else:
                    decision = int(input("Enter either 1 or 2: "))
                if decision == 1:
                    ds.mapit_generation_uri = mapit_generation_uri
                    ds.save()
                    division_set = ds
                if decision == 2:
                    start_date = datetime.strptime(
                        mapit_generation['created'].split('T')[0], "%Y-%m-%d")
                    ds.end_date = start_date - timedelta(days=1)
                    ds.save()
                    division_set = self._create_division_set(
                        organisation,
                        mapit_generation_uri, mapit_generation_start_date
                        )
        return division_set

    def carry_over_existing_divisions(self, organisation):
        print("Carrying over {}…".format(organisation))
        all_sets = organisation.divisionset.all().order_by('start_date')
        if all_sets.count() == 1:
            print("Only 1 set, carrying on")
            return

        for div_set in all_sets:
            try:
                newer_set = organisation.divisionset.filter(
                    start_date__gt=div_set.start_date
                    ).order_by('start_date').first()
            except OrganisationDivisionSet.DoesNotExist:
                print("No more sets")
                newer_set = None
            if not newer_set:
                return

            if not newer_set.mapit_generation_id:
                continue
            new_gen_id = int(newer_set.mapit_generation_id.split('/')[-1])
            carry_over = div_set.divisions.filter(
                mapit_generation_high__gte=new_gen_id)

            start_date = newer_set.start_date
            div_set.end_date = start_date - timedelta(days=1)
            div_set.save()


            for div in carry_over:
                try:
                    # Try to get the existing div for this set
                    newer_set.divisions.get(name=div.name)
                except OrganisationDivision.DoesNotExist:
                    # Make a new set
                    div.pk = None
                    div.divisionset = newer_set
                    div.save()

    def import_divisions(self, organisation, data):
        for mapit_id, division in data.items():
            division_set = self.get_division_set(organisation, division)
            self.create_single_division(division_set, organisation, division)
        self.carry_over_existing_divisions(organisation)

    def _import_area(self, org_type,
                     mapit_code, division_election_sub_type=''):
        print("Importing {}".format(org_type))
        org = Organisation.objects.get(organisation_type=org_type)
        regions_req = requests.get(
            "http://mapit.mysociety.org/areas/{}".format(mapit_code))
        for mapit_id, region in regions_req.json().items():
            division_set = self.get_division_set(org, region)
            self.create_single_division(
                division_set,
                org,
                region,
                division_election_sub_type=division_election_sub_type,
            )
        print("Finished importing {}".format(org_type))

    def import_ni_areas(self):
        """
        NIA doesn't have 'children' in MapIt, so we have to do this manually
        """
        self._import_area('nia', 'NIE')

    def import_parl_areas(self):
        self._import_area('parl', 'WMC')

    def import_gla_areas(self):
        self._import_area('gla', 'LAC', division_election_sub_type='c')

    def import_welsh_areas(self):
        """
        Because there are Welsh Assembly regions as well as Welsh Assembly
        constituencies, we can't use the 'children' link on 'Wales' (W08000001)
        """

        org = Organisation.objects.get(organisation_type='naw')

        regions_req = requests.get("http://mapit.mysociety.org/areas/WAE")
        for mapit_id, region in regions_req.json().items():
            division_set = self.get_division_set(org, region)
            self.create_single_division(
                division_set,
                org,
                region,
                division_election_sub_type='r'
            )
            req = requests.get(
                "http://mapit.mysociety.org/area/{}/children".format(
                    mapit_id
                ))
            for const_id, const in req.json().items():
                division_set = self.get_division_set(org, const)
                self.create_single_division(
                    division_set,
                    org,
                    const,
                    division_election_sub_type='c'
                )
        self.carry_over_existing_divisions(org)

    def import_scottish_areas(self):
        """
        See Wales.
        """
        org = Organisation.objects.get(organisation_type='sp')
        regions_req = requests.get("http://mapit.mysociety.org/areas/SPE")
        for mapit_id, region in regions_req.json().items():
            division_set = self.get_division_set(org, region)
            self.create_single_division(
                division_set,
                org,
                region,
                division_election_sub_type='r'
            )

            req = requests.get(
                "http://mapit.mysociety.org/area/{}/children".format(
                    mapit_id
                ))
            for const_id, const in req.json().items():
                division_set = self.get_division_set(org, const)
                self.create_single_division(
                    division_set,
                    org,
                    const,
                    division_election_sub_type='c'
                )
        self.carry_over_existing_divisions(org)
