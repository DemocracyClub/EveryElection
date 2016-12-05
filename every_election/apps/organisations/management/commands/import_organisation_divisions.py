import time

import requests
import requests_cache

requests_cache.install_cache('demo_cache')
CACHE = requests_cache.get_cache()

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from organisations.models import Organisation, OrganisationDivision
from organisations.constants import PARENT_TO_CHILD_AREAS


class Command(BaseCommand):
    skip_gss = [
        "E12000007",
        "W08000001"  # See import_welsh_areas
    ]

    def handle(self, **options):
        self.import_scottish_areas()
        self.import_gla_areas()
        self.import_parl_areas()
        self.import_ni_areas()
        self.import_welsh_areas()
        base = "http://mapit.mysociety.org"
        qs = Organisation.objects.exclude(gss='')
        qs = qs.exclude(gss__in=self.skip_gss)
        for organisation in qs:
            initial_url = "{}/area/{}".format(base, organisation.gss)
            print(initial_url)
            req = requests.get(initial_url)
            url = req.url

            child_type = PARENT_TO_CHILD_AREAS.get(req.json()['type'])
            req = requests.get("{}/children?type={}".format(url, child_type))

            if not CACHE.has_url(req.url):
                print("CACHE MISS")
                time.sleep(5)

            self.import_divisions(organisation, req.json())

    def import_divisions(self, organisation, data):
        for mapit_id, division in data.items():

            try:
                ons = division['codes'].get('ons')
                unit_id = division['codes'].get('unit_id')
                gss = division['codes'].get('gss')
                all_codes = [x for x in [ons, unit_id, gss] if x]

                official_identifier = all_codes[0]
            except:
                print(all_codes)
                print(division)

            OrganisationDivision.objects.update_or_create(
                official_identifier=official_identifier,
                organisation=organisation,
                defaults={
                    'gss': division['codes'].get('gss', ''),
                    'name': division['name'],
                    'slug': slugify(division['name']),
                    'division_type': division['type'],
                    'division_subtype': division['type_name'],
                }
            )

    def import_ni_areas(self):
        """
        NIA doesn't have 'children' in MapIt, so we have to do this manually
        """
        ni_org = Organisation.objects.get(organisation_type='nia')
        regions_req = requests.get("http://mapit.mysociety.org/areas/NIE")
        for mapit_id, region in regions_req.json().items():
            OrganisationDivision.objects.update_or_create(
                official_identifier=region['codes']['osni_oid'],
                organisation=ni_org,
                defaults={
                    'gss': region['codes'].get('gss', ''),
                    'name': region['name'],
                    'slug': slugify(region['name']),
                    'division_type': region['type'],
                    'division_subtype': region['type_name'],
                }
            )

    def import_parl_areas(self):
        parl_org = Organisation.objects.get(organisation_type='parl')
        regions_req = requests.get("http://mapit.mysociety.org/areas/WMC")
        for mapit_id, region in regions_req.json().items():
            print(region)
            OrganisationDivision.objects.update_or_create(
                official_identifier=region['codes'].get(
                    'unit_id', region['codes'].get('osni_oid')),
                organisation=parl_org,
                defaults={
                    'gss': region['codes'].get('gss', ''),
                    'name': region['name'],
                    'slug': slugify(region['name']),
                    'division_type': region['type'],
                    'division_subtype': region['type_name'],
                }
            )

    def import_gla_areas(self):
        gla_org = Organisation.objects.get(organisation_type='gla')
        regions_req = requests.get("http://mapit.mysociety.org/areas/LAC")
        for mapit_id, region in regions_req.json().items():
            print(region)
            OrganisationDivision.objects.update_or_create(
                official_identifier=region['codes'].get(
                    'unit_id', region['codes'].get('osni_oid')),
                organisation=gla_org,
                defaults={
                    'gss': region['codes'].get('gss', ''),
                    'name': region['name'],
                    'slug': slugify(region['name']),
                    'division_type': region['type'],
                    'division_subtype': region['type_name'],
                    'division_election_sub_type': 'c'
                }
            )


    def import_welsh_areas(self):
        """
        Because there are Welsh Assembly regions as well as Welsh Assembly
        constituencies, we can't use the 'children' link on 'Wales' (W08000001)
        """

        wales_org = Organisation.objects.get(organisation_type='naw')

        regions_req = requests.get("http://mapit.mysociety.org/areas/WAE")
        # time.sleep(1)
        for mapit_id, region in regions_req.json().items():
            OrganisationDivision.objects.update_or_create(
                official_identifier=region['codes']['unit_id'],
                organisation=wales_org,
                defaults={
                    'gss': region['codes'].get('gss', ''),
                    'name': region['name'],
                    'slug': slugify(region['name']),
                    'division_type': region['type'],
                    'division_subtype': region['type_name'],
                    'division_election_sub_type': 'r'
                }
            )
            req = requests.get("http://mapit.mysociety.org/area/{}/children".format(
                mapit_id
            ))
            # time.sleep(2)
            for const_id, const in req.json().items():
                OrganisationDivision.objects.update_or_create(
                    official_identifier=const['codes']['unit_id'],
                    organisation=wales_org,
                    defaults={
                        'gss': const['codes'].get('gss', ''),
                        'name': const['name'],
                        'slug': slugify(const['name']),
                        'division_type': const['type'],
                        'division_subtype': const['type_name'],
                        'division_election_sub_type': 'c'
                    }
                )

    def import_scottish_areas(self):
        """
        See Wales.
        """

        scot_org = Organisation.objects.get(organisation_type='sp')

        regions_req = requests.get("http://mapit.mysociety.org/areas/SPE")
        # time.sleep(1)
        for mapit_id, region in regions_req.json().items():
            OrganisationDivision.objects.update_or_create(
                official_identifier=region['codes']['unit_id'],
                organisation=scot_org,
                defaults={
                    'gss': region['codes'].get('gss', ''),
                    'name': region['name'],
                    'slug': slugify(region['name']),
                    'division_type': region['type'],
                    'division_subtype': region['type_name'],
                    'division_election_sub_type': 'r'
                }
            )
            req = requests.get("http://mapit.mysociety.org/area/{}/children".format(
                mapit_id
            ))
            # time.sleep(2)
            for const_id, const in req.json().items():
                OrganisationDivision.objects.update_or_create(
                    official_identifier=const['codes']['unit_id'],
                    organisation=scot_org,
                    defaults={
                        'gss': const['codes'].get('gss', ''),
                        'name': const['name'],
                        'slug': slugify(const['name']),
                        'division_type': const['type'],
                        'division_subtype': const['type_name'],
                        'division_election_sub_type': 'c'
                    }
                )

