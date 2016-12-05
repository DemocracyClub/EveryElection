import csv

import requests

from django.utils.text import slugify

from .models import Organisation
from elections.models import ElectedRole, ElectionType


def create_single(election_type, official_identifier,
                  organisation_type, defaults, subtypes=None):

    election_type = ElectionType.objects.get(election_type=election_type)
    elected_title = defaults.pop('elected_title')

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
        }
    )


def local_authority_eng_importer():
    url = "http://local-authority-eng.beta.openregister.org/records.tsv?page-size=5000"  # NOQA
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
            'territory_code': 'ENG',
            'elected_title': "Councillor for {}".format(line['official-name']),
            'election_name': "{} local election".format(line['official-name']),
        }

        create_single('local', line['local-authority-eng'],
                      "local-authority", defaults)
    add_gss_to_LAs()


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



