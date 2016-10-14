import os
import csv

from django.conf import settings
from django.utils.text import slugify

from .models import Organisation
from elections.models import ElectedRole, ElectionType


def local_authority_eng_importer():
    file_name = "local-authorities-eng.tsv"
    election_type = ElectionType.objects.get(election_type='local')

    data_file = csv.DictReader(
        open(os.path.join(settings.DATA_CACHE_DIR, file_name)),
        delimiter="\t")
    for line in data_file:
        slug = slugify(line['name'])
        organisation, _ = Organisation.objects.update_or_create(
            official_identifier=line['local-authority-eng'],
            organisation_type="local-authority",
            defaults={
                'official_name': line['official-name'],
                'common_name': line['name'],
                'organisation_subtype': line['local-authority-type'],
                'slug': slug,
                'territory_code': 'ENG',
            }
        )
        ElectedRole.objects.update_or_create(
            election_type=election_type,
            organisation=organisation,
            defaults={
                'elected_title':
                    "Councillor for {}".format(line['official-name']),
            }
        )


