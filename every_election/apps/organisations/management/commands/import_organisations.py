from django.core.management.base import BaseCommand

# import requests

# from organisations.models import Organisation
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
            'gss': 'S15000001',
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
            'gss': "E15000007",
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

        # self.add_missing_gss_codes()

    # def add_missing_gss_codes(self):
    #     """
    #     Some areas don't come with them. Add them from the register maps
    #     where possible
    #     """
    #
    #     if not getattr(self, 'register_gss_map', None):
    #         req = requests.get("https://raw.githubusercontent.com/openregister/local-authority-data/master/maps/gss.tsv")  # noqa
    #         self.register_gss_map = {}
    #         for map_line in req.text.splitlines():
    #             map_line = map_line.split('\t')
    #             if map_line[0] == "gss":
    #                 continue
    #             self.register_gss_map[map_line[1]] = map_line[0]
    #
    #
    #     for org in Organisation.objects.filter(gss=''):
    #         org_register_curie = "{}:{}".format(
    #             "{}-{}".format(
    #                 org.organisation_type,
    #                 org.territory_code.lower()
    #             ),
    #             org.official_identifier
    #         )
    #         import ipdb; ipdb.set_trace()

    # # Lords
    # TODO
    # defaults={
    #     'official_name': "House of Lords of the United Kingdom",
    #     'common_name': "House of Lords",
    #     'slug': 'hol',
    #     'elected_title': "Lord",
    # }
    # create_single('parl', 'parl-hol', "parl", defaults)
