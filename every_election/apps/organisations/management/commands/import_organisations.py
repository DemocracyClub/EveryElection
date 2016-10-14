from django.core.management.base import BaseCommand
from django.conf import settings

from organisations.models import Organisation
from organisations.importers import local_authority_eng_importer
from elections.models import ElectedRole, ElectionType


class Command(BaseCommand):
    def handle(self, **options):

        # Local Authorities England
        local_authority_eng_importer()

        # TODO: Local Authorities Wales

        # TODO: Local Authorities Scotland

        # TODO: Police force

        # TODO: GLA

        # TODO: Mayors


        # Parl
        organisation, _ = Organisation.objects.update_or_create(
            official_identifier='parl-hoc',
            organisation_type="parl",
            defaults={
                'official_name': "House of Commons of the United Kingdom",
                'common_name': "House of Commons",
                'slug': 'parl',
            }
        )
        election_type = ElectionType.objects.get(election_type='parl')
        ElectedRole.objects.update_or_create(
            election_type=election_type,
            organisation=organisation,
            defaults={'elected_title': "Member of Parliament",}
        )


        # # Lords
        # TODO
        # Organisation.objects.update_or_create(
        #     official_identifier='parl-hol',
        #     organisation_type="parl",
        #     defaults={
        #         'official_name': "House of Lords of the United Kingdom",
        #         'common_name': "House of Lords",
        #         'slug': 'lords',
        #     }
        # )

