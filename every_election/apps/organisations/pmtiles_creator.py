import subprocess

from django.db import connection
from organisations.models import DivisionGeography


class PMtilesCreator:
    def __init__(self, divset):
        div_subtypes = divset.divisions.values("division_subtype").distinct()
        if div_subtypes.count() > 1:
            raise NotImplementedError(
                "PMTiles creation is not implemented for multiple division subtypes."
            )
        self.divset = divset

    def create_pmtile(self, dest_dir):
        pmtiles_fp = f"{dest_dir}/{self.divset.pmtiles_file_name}"

        geojson_fp = self.create_geojson(dest_dir)
        tippecanoe_command = f"tippecanoe -o {pmtiles_fp} -zg --drop-rate=2 --drop-densest-as-needed {geojson_fp} -l {self.divset.id}"
        subprocess.run(tippecanoe_command, shell=True, check=True)

        return pmtiles_fp

    def create_geojson(self, dest_dir):
        geojson_fp = f"{dest_dir}/{self.divset.id}.geojson"
        ogr_command = self.construct_ogr_command(geojson_fp)
        subprocess.run(ogr_command, shell=True, check=True)
        return geojson_fp

    def construct_ogr_command(self, geojson_fp):
        db_settings = connection.settings_dict
        sql_query = self.construct_sql_query(self.divset.id)

        db_connection_string = (
            f"dbname={db_settings['NAME']} "
            f"user={db_settings['USER']} "
            f"password={db_settings['PASSWORD']} "
            f"host={db_settings['HOST'] if db_settings['HOST'] else '127.0.0.1'} "
            f"port={db_settings['PORT'] if db_settings['PORT'] else '5432'}"
        )

        return (
            f'ogr2ogr -f "GeoJSON" {geojson_fp} '
            f'"PG:{db_connection_string}" '
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
                "division__official_identifier",
            )
            .query.sql_with_params()
        )
        sql = sql.replace("::bytea", "")  # Remove bytea typecast
        return sql % params  # Substitute parameters into the SQL query
