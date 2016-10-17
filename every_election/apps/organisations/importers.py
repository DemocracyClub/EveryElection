import os
import csv

from django.conf import settings
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
    file_name = "local-authorities-eng.tsv"

    data_file = csv.DictReader(
        open(os.path.join(settings.DATA_CACHE_DIR, file_name)),
        delimiter="\t")
    for line in data_file:

        defaults = {
            'official_name': line['official-name'],
            'common_name': line['name'],
            'organisation_subtype': line['local-authority-type'],
            'slug': slugify(line['name']),
            'territory_code': 'ENG',
            'elected_title': "Councillor for {}".format(line['official-name']),
        }

        create_single('local', line['local-authority-eng'],
                      "local-authority", defaults)
