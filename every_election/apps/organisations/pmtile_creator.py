import subprocess

from django.db import connection
from organisations.models import DivisionGeography


class PMtileCreator:
    def __init__(self, divset):
        self.divset = divset

    def create_pmtile(self, dest_dir):
        pmtiles_fp = f"{dest_dir}/{self.divset.pmtiles_file_name}"

        try:
            geojson_fp = self.extract_geojson(dest_dir)
            # TODO: choose sensible layer name
            tippecanoe_command = f"tippecanoe -o {pmtiles_fp} -zg --drop-rate=2 --drop-densest-as-needed {geojson_fp} -l {self.divset.id}"
            subprocess.run(tippecanoe_command, shell=True, check=True)

            return pmtiles_fp
        except subprocess.CalledProcessError as e:
            # TODO: handle this error better
            print(f"Error creating pmtile: {e}")

    def extract_geojson(self, dest_dir):
        geojson_fp = f"{dest_dir}/{self.divset.id}.geojson"
        ogr_command = self.construct_ogr_command(geojson_fp)
        subprocess.run(ogr_command, shell=True, check=True)
        return geojson_fp

    def construct_ogr_command(self, geojson_fp):
        db_settings = connection.settings_dict
        sql_query = self.construct_sql_query(self.divset.id)

        return (
            f'ogr2ogr -f "GeoJSON" {geojson_fp} '
            f'"PG:dbname={db_settings["NAME"]} user={db_settings["USER"]} password={db_settings["PASSWORD"]} host={db_settings["HOST"]} port={db_settings["PORT"]}" '
            f'-sql "{sql_query}"'
        )

    def construct_sql_query(self, divisionset_id):
        sql, params = (
            DivisionGeography.objects.filter(
                division__divisionset_id=divisionset_id
            )
            .select_related("division")
            .values(
                "id",
                "geography",
                "source",
                "division_id",
                "division__name",
            )
            .query.sql_with_params()
        )
        sql = sql.replace("::bytea", "")  # Remove bytea typecast
        return sql % params  # Substitute parameters into the SQL query
