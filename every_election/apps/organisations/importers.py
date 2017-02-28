import csv

import requests

from django.utils.text import slugify

from .models import Organisation
from elections.models import ElectedRole, ElectionType
from organisations import constants


def create_single(election_type, official_identifier,
                  organisation_type, defaults, subtypes=None):

    election_type = ElectionType.objects.get(election_type=election_type)
    elected_title = defaults.pop('elected_title', None)
    elected_role_name = defaults.pop('elected_role_name', elected_title)

    organisation, _ = Organisation.objects.update_or_create(
        official_identifier=official_identifier,
        organisation_type=organisation_type,
        defaults=defaults
    )

    ElectedRole.objects.update_or_create(
        election_type=election_type,
        organisation=organisation,
        defaults={
            'elected_title': elected_title,
            'elected_role_name': elected_role_name,
        }
    )


def base_local_authority_importer(territory_code, url):
    req = requests.get(url)

    data_file = csv.DictReader(
        req.text.splitlines(),
        delimiter="\t")

    for line in data_file:
        defaults = {
            'official_name': line['official-name'],
            'common_name': line['name'],
            'organisation_subtype': line['local-authority-type'],
            'slug': slugify(line['name']),
            'territory_code': territory_code.upper(),
            'elected_title': "Local Councillor",
            'elected_role_name': "Councillor for {}".format(line['official-name']),
            'election_name': "{} local election".format(line['name']),
        }

        create_single('local',
                      line["local-authority-{}".format(territory_code)],
                      "local-authority", defaults)
    add_gss_to_LAs()


def local_authority_eng_importer():
    url = "https://local-authority-eng.beta.openregister.org/records.tsv?page-size=5000"  # NOQA
    base_local_authority_importer("eng", url)


def local_authority_wls_importer():
    url = "https://local-authority-wls.discovery.openregister.org/records.tsv?page-size=5000"  # NOQA
    base_local_authority_importer("wls", url)


def local_authority_nir_importer():
    url = "https://local-authority-nir.discovery.openregister.org/records.tsv?page-size=5000"  # NOQA
    base_local_authority_importer("nir", url)


def local_authority_sct_importer():
    url = "https://local-authority-sct.discovery.openregister.org/records.tsv?page-size=5000"  # NOQA
    base_local_authority_importer("sct", url)


def add_gss_to_LAs():
    url = "https://raw.githubusercontent.com/openregister/local-authority-data/master/maps/gss.tsv"  # NOQA
    req = requests.get(url)
    map_file = csv.DictReader(
        req.text.splitlines(),
        delimiter="\t")
    code_to_gss = {m['local-authority'].split(':')[1]: m['gss']
                   for m in map_file}
    for code, gss in code_to_gss.items():
        try:
            la =  Organisation.objects.get(official_identifier=code)
            la.gss = gss
            la.save()
        except Organisation.DoesNotExist:
            pass


def police_importer():
    url = "https://data.police.uk/api/forces"
    req = requests.get(url)

    for force in req.json():
        if force['id'] in constants.AREAS_WITHOUT_PCCS:
            continue

        if force['id'] in constants.AREAS_IN_WALES:
            territory_code = "WLS"
        else:
            territory_code = "ENG"

        defaults = {
            'official_name': force['name'],
            'common_name': force['name'],
            'slug': force['id'],
            'territory_code': territory_code,
            'elected_title': "Police and Crime Commissioner",
            'elected_role_name': "Police and Crime Commissioner for {}".format(
                force['name']
            ),
        }
        create_single('pcc', force['id'], 'police_area', defaults)

def mayor_importer():
    orgs_with_mayors = [
        {
         'org': "Greater London Authority",
         'elected_role_name': "Mayor of London",
         'slug': 'london',
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
        {
         'org': "West Midlands Combined Authority",
         'elected_role_name': "Mayor of West Midlands Combined Authority",
         'slug': 'west-midlands',
         'territory_code': 'ENG',
         'organisation_type': 'combined-authority',
        },
        {
         'org': "Greater Manchester",
         'elected_role_name': "Mayor of Greater Manchester",
         'slug': 'greater-manchester',
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
        {
         'org': "Liverpool City Region",
         'elected_role_name': "Mayor of Liverpool City Region",
         'slug': "liverpool",
         'territory_code': 'ENG',
         'organisation_type': 'combined-authority',
        },
        {
         'org': "Cambridgeshire and Peterborough Combined Authority",
         'elected_role_name': "Mayor of Cambridgeshire and Peterborough Combined Authority",
         'slug': "cambridgeshire-and-peterborough",
         'territory_code': 'ENG',
         'organisation_type': 'combined-authority',
        },
        {
         'org': "West of England Combined Authority",
         'elected_role_name': "Mayor of West of England Combined Authority",
         'slug': "west-of-england",
         'territory_code': 'ENG',
         'organisation_type': 'combined-authority',
        },
        {
         'org': "Tees Valley Combined Authority",
         'elected_role_name': "Mayor of Tees Valley Combined Authority",
         'slug': "tees-valley",
         'territory_code': 'ENG',
         'organisation_type': 'combined-authority',
        },
        {
         'org': "North Tyneside Council",
         'org_id': 'NTY',
         'elected_role_name': "Mayor of Tees Valley Combined Authority",
         'slug': "north-tyneside",
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
        {
         'org': "Doncaster Metropolitan Borough Council",
         'org_id': 'DNC',
         'elected_role_name': "Mayor of Doncaster Metropolitan Borough Council",
         'slug': "doncaster",
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
    ]
    for org_data in orgs_with_mayors:
        defaults = {
            'official_name': org_data['org'],
            'common_name': org_data['org'],
            'slug': org_data['slug'],
            'territory_code': org_data.get('territory_code'),
            'elected_title': "Mayor",
            'elected_role_name': org_data['elected_role_name'],
            'election_name': org_data['org']
        }
        create_single(
            'mayor',
            org_data.get('org_id', org_data['slug']),
            org_data['organisation_type'],
            defaults
        )
