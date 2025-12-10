import subprocess
import sys
from pathlib import Path

import psycopg2
from django.db import connection
from organisations.constants import PMTILES_FEATURE_ATTR_FIELDS
from organisations.models import DivisionGeography


class PMtilesCreator:
    """
    PMtilesCreator is a utility class for generating a PMTiles file from a DivisionSet.

    Args:
        divset:  a DivisionSet model instance.

    Methods:
        create_pmtile(dest_dir):
            Generates a PMTiles file in the specified destination directory by exporting division geographies
            as GeoJSON and combining them using tippecanoe
    """

    feature_fields = PMTILES_FEATURE_ATTR_FIELDS

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
            geojson_fp = self._create_geojson(dest_dir, div_type)
            geojson_files.append(geojson_fp)

        tippecanoe_path = Path(sys.prefix) / "bin" / "tippecanoe"
        tippecanoe_command = f"{tippecanoe_path} -o {pmtiles_fp} -zg --drop-rate=2 --drop-densest-as-needed {' '.join(geojson_files)}"

        subprocess.run(tippecanoe_command, shell=True, check=True)

        return pmtiles_fp

    def _create_geojson(self, dest_dir, div_type):
        geojson_fp = f"{dest_dir}/{self.divset.id}_{div_type}.geojson"
        ogr_command = self._construct_ogr_command(geojson_fp, div_type)
        subprocess.run(ogr_command, shell=True, check=True)
        return geojson_fp

    def _construct_ogr_command(self, geojson_fp, div_type):
        db_settings = connection.settings_dict
        sql_query = self._construct_sql_query_string(self.divset.id, div_type)

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

    def _construct_sql_query_string(self, divisionset_id, div_type):
        qs = self._get_queryset(divisionset_id).filter(
            division__division_type=div_type
        )
        sql, params = qs.query.sql_with_params()

        sql = sql.replace("::bytea", "")  # Remove bytea typecast

        # Format params for SQL string substitution
        formatted_params = tuple(
            psycopg2.extensions.adapt(p).getquoted().decode()
            if isinstance(p, str)
            else p
            for p in params
        )
        return sql % formatted_params  # Substitute params into the SQL query

    def _get_queryset(self, divisionset_id):
        return (
            DivisionGeography.objects.filter(
                division__divisionset_id=divisionset_id,
            )
            .select_related("division")
            .values(
                *self.feature_fields,
                "geography",
            )
        )
