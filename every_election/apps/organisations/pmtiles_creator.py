import subprocess

import psycopg2
from django.db import connection
from organisations.models import DivisionGeography


class PMtilesCreator:
    def __init__(self, divset):
        self.divset = divset

    def create_pmtile(self, dest_dir):
        pmtiles_fp = f"{dest_dir}/{self.divset.pmtiles_file_name}"
        # Create a geojson file for each division subtype
        div_types = set(
            self.divset.divisions.values_list("division_type", flat=True)
        )
        geojson_files = []
        for div_type in div_types:
            geojson_fp = self.create_geojson(dest_dir, div_type)
            geojson_files.append(geojson_fp)

        tippecanoe_command = f"tippecanoe -o {pmtiles_fp} -zg --drop-rate=2 --drop-densest-as-needed {' '.join(geojson_files)}"
        subprocess.run(tippecanoe_command, shell=True, check=True)

        return pmtiles_fp

    def create_geojson(self, dest_dir, div_type):
        geojson_fp = f"{dest_dir}/{self.divset.id}_{div_type}.geojson"
        ogr_command = self.construct_ogr_command(geojson_fp, div_type)
        subprocess.run(ogr_command, shell=True, check=True)
        return geojson_fp

    def construct_ogr_command(self, geojson_fp, div_type):
        db_settings = connection.settings_dict
        sql_query = self.construct_sql_query(self.divset.id, div_type)

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

    def construct_sql_query(self, divisionset_id, div_type):
        sql, params = (
            DivisionGeography.objects.filter(
                division__divisionset_id=divisionset_id,
                division__division_type=div_type,
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

        # Format params for SQL
        formatted_params = tuple(
            psycopg2.extensions.adapt(p).getquoted().decode()
            if isinstance(p, str)
            else p
            for p in params
        )
        return sql % formatted_params  # Substitute params into the SQL query
