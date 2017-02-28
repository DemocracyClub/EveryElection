from django.core.management.base import BaseCommand

from organisations.models import Organisation
from organisations.importers import (
    local_authority_eng_importer,
    local_authority_wls_importer,
    local_authority_sct_importer,
    local_authority_nir_importer,
    police_importer,
    mayor_importer,
    create_single)


class Command(BaseCommand):
    def handle(self, **options):

        # Mayors
        mayor_importer()

        # Police
        police_importer()

        # Local Authorities England
        local_authority_eng_importer()
        local_authority_wls_importer()
        local_authority_sct_importer()
        local_authority_nir_importer()


        # NAW
        defaults={
            'gss': 'W08000001',
            'official_name': "Welsh assembly",
            'common_name': "Welsh assembly",
            'slug': 'naw',
            'territory_code': 'WLS',
            'elected_title': "Assembly Member",
            'election_name': "National Assembly for Wales election",
        }
        create_single('naw', 'naw', "naw", defaults)

        # NIA
        defaults={
            'gss': 'N07000001',
            'official_name': "Northern Ireland assembly",
            'common_name': "Northern Ireland assembly",
            'slug': 'nia',
            'territory_code': 'NIR',
            'elected_title': "Assembly Member",
            'election_name': "Northern Ireland assembly election",
        }
        create_single('nia', 'nia', "nia", defaults)

        # sp
        defaults={
            'official_name': "Scottish Parliament",
            'common_name': "Scottish Parliament",
            'slug': 'sp',
            'territory_code': 'SCT',
            'elected_title': "Member of the Scottish Parliament",
            'election_name': "Scottish parliament election",
        }
        create_single('sp', 'sp', "sp", defaults)

        # gla
        defaults={
            'official_name': "Greater London assembly",
            'common_name': "Greater London assembly",
            'slug': 'gla',
            'territory_code': 'ENG',
            'elected_title': "Assembly Member",
            'election_name': "London Assembly election",
        }
        create_single('gla', 'gla', "gla", defaults)


        # Parl
        defaults={
            'official_name': "House of Commons of the United Kingdom",
            'common_name': "House of Commons",
            'slug': 'parl',
            'territory_code': 'GBN',
            'elected_title': "Member of Parliament",
            'election_name': "UK general election",

        }
        create_single('parl', 'parl-hoc', "parl", defaults)



        # # Lords
        # TODO
        # defaults={
        #     'official_name': "House of Lords of the United Kingdom",
        #     'common_name': "House of Lords",
        #     'slug': 'hol',
        #     'elected_title': "Lord",
        # }
        # create_single('parl', 'parl-hol', "parl", defaults)

