import csv
from difflib import ndiff
import requests

from django.contrib.gis.gdal import DataSource
from django.db import transaction
from django.utils.text import slugify

from .models import (
    Organisation,
    OrganisationDivisionSet,
    OrganisationDivision,
    DivisionGeography,
)
from elections.models import ElectedRole, ElectionType
from organisations import constants
from storage.shapefile import pre_process_layer


class DiffException(Exception):

    def __init__(self, message, diff):
        super().__init__(message)
        self.diff = diff


class DivisionSetGeographyImporter:

    def __init__(self, data, division_set, name_column='name', name_map={}, srid=27700):
        if not isinstance(data, DataSource):
            error = "param 'data' must be an instance of django.contrib.gis.gdal.DataSource"
            raise TypeError(error)
        if len(data) != 1:
            raise ValueError("Expected 1 layer, found %i" % (len(data)))
        self.data = data[0]

        self.name_column = name_column

        if not isinstance(division_set, OrganisationDivisionSet):
            error = "param 'division_set' must be an instance of organisations.models.OrganisationDivisionSet"
            raise TypeError(error)
        self.div_set = division_set

        if not isinstance(name_map, dict):
            raise TypeError("param 'name_map' must be an instance of dict")
        self.name_map = name_map

        if not isinstance(srid, int):
            raise TypeError("param 'srid' must be an instance of int")
        self.srid = srid

    def get_name(self, division):
        name = division[self.name_column].value
        if name in self.name_map:
            return self.name_map[name]
        return name

    def check_names(self):
        legislation_names = sorted([div.name for div in self.div_set.divisions.all()])
        boundary_names = sorted([self.get_name(div) for div in self.data])

        if len(legislation_names) != len(boundary_names):
            raise ValueError("Expected %i boundaries in input file, found %i"\
                % (len(legislation_names), len(boundary_names)))
        if legislation_names != boundary_names:
            # create a 'diff' of the 2 lists
            # so we can work out what we need to fix
            diff = ndiff(legislation_names, boundary_names)
            raise DiffException("legislation_names != boundary_names", diff)

        return True

    def build_objects(self):
        div_geogs = []
        for feature in self.data:
            name = self.get_name(feature)
            division = OrganisationDivision.objects.get(
                divisionset=self.div_set, name=name)
            div_geogs.append(
                DivisionGeography(
                    division=division,
                    organisation=None,
                    geography=feature.multipolygon
                )
            )
        return div_geogs

    @transaction.atomic
    def save_all(self, objects):
        for record in objects:
            record.save()

    def import_data(self):
        self.data = pre_process_layer(self.data, self.srid)
        self.check_names()
        div_geogs = self.build_objects()
        self.save_all(div_geogs)
        return


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


def base_local_authority_importer(territory_code,
                                  url, code_field, org_type=None,
                                  official_name_field='official-name'):
    req = requests.get(url)

    data_file = csv.DictReader(
        req.text.splitlines(),
        delimiter="\t")

    for line in data_file:
        defaults = {
            'official_name': line[official_name_field],
            'common_name': line['name'],
            'slug': slugify(line['name']),
            'territory_code': territory_code.upper(),
            'elected_title': "Local Councillor",
            'elected_role_name': "Councillor for {}".format(
                line[official_name_field]),
            'election_name': "{} local election".format(line['name']),
        }
        try:
            defaults['organisation_subtype'] = line['local-authority-type']
        except KeyError:
            if org_type:
                defaults['organisation_subtype'] = org_type
            else:
                raise

        create_single('local', line[code_field], "local-authority", defaults)
    add_gss_to_LAs()


def local_authority_eng_importer():
    base_local_authority_importer(
        "eng", constants.ENGLAND_REGISTER_URL, 'local-authority-eng')


def local_authority_wls_importer():
    base_local_authority_importer(
        "wls", constants.WALES_REGISTER_URL, 'principal-local-authority', 'UA')


def local_authority_nir_importer():
    base_local_authority_importer(
        "nir", constants.NI_REGISTER_URL, 'local-authority-nir',
        official_name_field='name')
    overload_gss_code = {
        'NIR-A': '95A',
        'NIR-B': '95B',
        'NIR-C': '95C',
        'NIR-D': '95D',
        'NIR-E': '95E',
        'NIR-F': '95F',
        'NIR-G': '95G',
        'NIR-H': '95H',
        'NIR-I': '95I',
        'NIR-J': '95J',
        'NIR-K': '95K',
        'NIR-L': '95L',
        'NIR-M': '95M',
        'NIR-N': '95N',
        'NIR-O': '95O',
        'NIR-P': '95P',
        'NIR-Q': '95Q',
        'NIR-R': '95R',
        'NIR-S': '95S',
        'NIR-T': '95T',
        'NIR-U': '95U',
        'NIR-V': '95V',
        'NIR-W': '95W',
        'NIR-X': '95X',
        'NIR-Y': '95Y',
    }

    for official_identifier, code in overload_gss_code.items():
        Organisation.objects.filter(
            official_identifier=official_identifier, gss="").update(
                gss=code)


def local_authority_sct_importer():
    base_local_authority_importer(
        "sct", constants.SCOTLAND_REGISTER_URL, 'local-authority-sct')


def add_gss_to_LAs():
    url = constants.REGISTER_GSS_URL
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
    url = constants.POLICE_FORCES_URL
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
         'slug': 'greater-manchester-ca',
         'territory_code': 'ENG',
         'organisation_type': 'combined-authority',
        },
        {
         'org': "Liverpool City Region",
         'elected_role_name': "Mayor of Liverpool City Region",
         'slug': "liverpool-city-ca",
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
        {
         'org': "Bedford Borough Council",
         'org_id': "BDF",
         'elected_role_name': "Mayor of Bedford",
         'slug': "bedford",
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
        {
         'org': "Bristol City Council",
         'org_id': "BST",
         'elected_role_name': "Mayor of Bristol",
         'slug': "bristol",
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
        {
         'org': "Copeland Borough Council",
         'org_id': "COP",
         'elected_role_name': "Mayor of Copeland",
         'slug': "copeland",
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
        {
         'org': "London Borough of Hackney",
         'org_id': "HCK",
         'elected_role_name': "Mayor of Hackney",
         'slug': "hackney",
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
        {
         'org': "Leicester City Council",
         'org_id': "LCE",
         'elected_role_name': "Mayor of Leicester",
         'slug': "leicester",
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
        {
         'org': "London Borough of Lewisham",
         'org_id': "LEW",
         'elected_role_name': "Mayor of Lewisham",
         'slug': "lewisham",
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
        {
         'org': "Liverpool City Council",
         'org_id': 'LIV',
         'elected_role_name': "Mayor of Liverpool",
         'slug': "liverpool",
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
        {
         'org': "Mansfield District Council",
         'org_id': "MAS",
         'elected_role_name': "Mayor of Mansfield",
         'slug': "mansfield",
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
        {
         'org': "Middlesbrough Borough Council",
         'org_id': "MDB",
         'elected_role_name': "Mayor of Middlesbrough",
         'slug': "middlesbrough",
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
        {
         'org': "London Borough of Newham",
         'org_id': 'NWM',
         'elected_role_name': "Mayor of Newham",
         'slug': "newham",
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
        {
         'org': "Salford City Council",
         'org_id': "SLF",
         'elected_role_name': "Mayor of Salford",
         'slug': "salford",
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
        {
         'org': "Torbay Council",
         'org_id': "TOB",
         'elected_role_name': "Mayor of Torbay",
         'slug': "torbay",
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
        {
         'org': "London Borough of Tower Hamlets",
         'org_id': "TWH",
         'elected_role_name': "Mayor of Tower Hamlets",
         'slug': "tower-hamlets",
         'territory_code': 'ENG',
         'organisation_type': 'local-authority',
        },
        {
         'org': "Watford Borough Council",
         'org_id': "WAT",
         'elected_role_name': "Mayor of Watford",
         'slug': "watford",
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
