import os
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Export divisions as GeoJSON and create a pmtile using ogr2ogr and tippecanoe"

    def add_arguments(self, parser):
        parser.add_argument(
            "divisionset_id",
            type=str,
            help="The ID of the divisionset to export",
        )

    def handle(self, *args, **options):
        self.divisionset_id = options["divisionset_id"]
        geojson_fp = f"{self.data_path}/{self.divisionset_id}_divisions.geojson"
        pmtiles_fp = f"{self.data_path}/{self.divisionset_id}_divisions.pmtiles"

        # Construct the commands
        ogr_command = self.construct_ogr_command(geojson_fp)
        tippecanoe_command = f"tippecanoe -o {pmtiles_fp} -zg --drop-rate=2 --drop-densest-as-needed {geojson_fp}"

        # Execute the commands
        try:
            subprocess.run(ogr_command, shell=True, check=True)
            subprocess.run(tippecanoe_command, shell=True, check=True)

            # Clean up temporary files
            os.remove(geojson_fp)
            self.stdout.write(
                self.style.SUCCESS(f"Successfully created pmtile {pmtiles_fp}")
            )
        except subprocess.CalledProcessError as e:
            self.stderr.write(
                self.style.ERROR(f"Error exporting divisions: {e}")
            )
            return  # return early on error

    def construct_ogr_command(self, geojson_fp):
        # Get database connection settings from Django's connection object
        db_settings = connection.settings_dict
        dbname = db_settings["NAME"]
        user = db_settings["USER"]
        password = db_settings["PASSWORD"]
        host = db_settings["HOST"]
        port = db_settings["PORT"]

        sql_query = self.construct_sql_query()

        return (
            f'ogr2ogr -f "GeoJSON" {geojson_fp} '
            f'"PG:dbname={dbname} user={user} password={password} host={host} port={port}" '
            f'-sql "{sql_query}"'
        )

    def construct_sql_query(self):
        # TODO: get query from database
        return (
            "SELECT g.*, d.name as division_name, d.id as division_id "
            "FROM organisations_divisiongeography g "
            "JOIN organisations_organisationdivision d ON g.division_id = d.id "
            f"WHERE d.divisionset_id = '{self.divisionset_id}'"
        )

    @property
    def data_path(self):
        if getattr(settings, "PRIVATE_DATA_PATH", None):
            path = settings.PRIVATE_DATA_PATH
        else:
            pass
        # TODO: use s3 on prod look at lgbce_review_helper for help writing to s
        # s3 = S3Wrapper()
        # path = s3.data_path
        return os.path.abspath(path)
