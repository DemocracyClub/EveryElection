import datetime

from core.mixins import ReadFromFileMixin
from django.contrib.gis.gdal import DataSource
from django.core.management import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from organisations.models import (
    DivisionGeography,
    Organisation,
    OrganisationDivision,
    OrganisationDivisionSet,
)
from storage.shapefile import pre_process_layer

TERRITORY_LOOKUP = {
    "england": "ENG",
    "northern ireland": "NIR",
    "scotland": "SCT",
    "wales": "WLS",
}


class Command(ReadFromFileMixin, BaseCommand):
    help = """You probably don't want to use this for anything apart from a national body. 
    For local authorities you should probably be importing from an electoral change order, by using import_divisionsets_from_csv, 
    and then attaching boundaries with import_lgbce.
    If you have a shapefile or geopackage containing names, official identifiers, territories and geometries of a divsionset, then 
    this command imports them, creating a new divisionset for them. 
    Example call: 
    python manage.py import_divisionset_from_geodata \
        -f ~/Downloads/parl_constituencies_2025.gpkg   
        --org-id 499 --srid 4326 --short-title "2025 Boundaries"    
        --id-field gss_code --name-field name --division-type WMC \
        --division-subtype "UK Parliament constituency" --territory-field nation \
        --source "mySociety: UK Parliamentary Constituencies 2025"
    """

    def __init__(
        self, stdout=None, stderr=None, no_color=False, force_color=False
    ):
        super().__init__(stdout, stderr, no_color, force_color)
        self.source = None
        self.territory_field = None
        self.division_set = None
        self.division_subtype = None
        self.division_geographies = []
        self.division_type = None
        self.name_field = None
        self.id_field = None
        self.divisions = []
        self.org = None
        self.srid = None
        self.data = None

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--org-id", action="store", help="Organisation EE ID"
        )
        parser.add_argument(
            "--srid",
            help="SRID (co-ordinates system) used by the input file (default = 27700)",
            choices=["27700", "4326"],
        )
        parser.add_argument(
            "--short-title", action="store", help="Short title for DivisionSet"
        )
        parser.add_argument(
            "--id-field", action="store", help="ID field in datasource"
        )
        parser.add_argument(
            "--name-field", action="store", help="Name field in datasource"
        )
        parser.add_argument(
            "--territory-field",
            action="store",
            help="Territory field in datasource",
        )
        parser.add_argument(
            "--division-type",
            action="store",
            help="Division Type being imported",
        )
        parser.add_argument(
            "--division-subtype",
            action="store",
            help="Division Sub Type being imported",
        )
        parser.add_argument(
            "--source",
            action="store",
            help="Source for data being imported",
        )

    def get_datasource(self, options):
        tmp_file = self.load_data(options)
        return DataSource(tmp_file)

    def validate_data_source(self, datasource):
        if not isinstance(datasource, DataSource):
            error = "param 'data' must be an instance of django.contrib.gis.gdal.DataSource"
            raise TypeError(error)
        if len(datasource) != 1:
            raise ValueError("Expected 1 layer, found %i" % (len(datasource)))
        self.data = datasource[0]

    def create_divisionset(self, start_date, short_title):
        self.division_set = OrganisationDivisionSet(
            organisation=self.org,
            start_date=start_date,
            short_title=short_title,
        )
        self.division_set.save()

    def name_to_id(self, feature):
        name = self.get_name(feature)
        name = name.replace("&", "and")
        name = name.strip()
        return slugify(name)

    def get_id(self, feature):
        identifier = feature[self.id_field].value
        if not identifier:
            identifier = (
                f"{self.org.official_identifier}:{self.name_to_id(feature)}"
            )
        return identifier

    def get_name(self, feature):
        return feature[self.name_field].value

    def get_territory_code(self, feature):
        territory_code = feature[self.territory_field].value
        if territory_code not in ["ENG", "NIR", "SCT", "WLS"]:
            territory_code = TERRITORY_LOOKUP[territory_code.lower()]
        return territory_code

    def create_division(self, feature):
        identifier = self.get_id(feature)
        name = self.get_name(feature)
        return OrganisationDivision(
            official_identifier=identifier,
            temp_id=identifier,
            name=name,
            slug=slugify(name),
            division_type=self.division_type,
            division_subtype=self.division_subtype,
            divisionset=self.division_set,
            territory_code=self.get_territory_code(feature),
        )

    def create_divisions(self):
        for feature in self.data:
            self.divisions.append(self.create_division(feature))

    @transaction.atomic
    def save_divisions(self):
        for div in self.divisions:
            div.save()

    def create_division_geographies(self):
        for feature in self.data:
            self.division_geographies.append(
                self.create_division_geography(feature)
            )

    def create_division_geography(self, feature):
        division = OrganisationDivision.objects.get(
            divisionset=self.division_set,
            official_identifier=self.get_id(feature),
        )
        return DivisionGeography(
            division=division,
            geography=feature.multipolygon,
            source=self.source,
        )

    @transaction.atomic
    def save_division_geographies(self):
        for div_geog in self.division_geographies:
            div_geog.save()

    def handle(self, *args, **options):
        self.org = Organisation.objects.get(pk=options["org_id"])
        self.current_divset = self.org.divisionset.get()
        if not self.current_divset.end_date:
            self.stdout.write(
                f"No end_date set on current divisionset ({self.org}: {self.current_divset}). "
            )
            return

        start_date = self.current_divset.end_date + datetime.timedelta(days=1)
        short_title = options["short_title"]
        self.create_divisionset(start_date, short_title)

        self.validate_data_source(self.get_datasource(options))
        self.data = pre_process_layer(self.data, int(options["srid"]))
        self.id_field = options["id_field"]
        self.name_field = options["name_field"]
        self.territory_field = options["territory_field"]
        self.division_type = options["division_type"]
        self.division_subtype = options.get("division_subtype", None)
        self.source = options["source"]
        self.create_divisions()
        self.save_divisions()
        self.create_division_geographies()
        self.save_division_geographies()
