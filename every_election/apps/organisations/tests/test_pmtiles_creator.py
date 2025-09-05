import json
import os
from tempfile import TemporaryDirectory

from django.test import TransactionTestCase
from factories import (
    DivisionGeographyFactory,
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
)
from organisations.pmtiles_creator import PMtilesCreator


class TestPMtilesCreator(TransactionTestCase):
    def setUp(self):
        self.divisionset = OrganisationDivisionSetFactory()
        for _ in range(5):  # Create five divisions for the divisionset
            div = OrganisationDivisionFactory(divisionset=self.divisionset)
            DivisionGeographyFactory(division=div)
        self.pmtile_creator = PMtilesCreator(self.divisionset)

    def test_create_pmtiles_file_single_div_type(self):
        with TemporaryDirectory() as temp_dir:
            pm_tile_fp = self.pmtile_creator.create_pmtile(temp_dir)

            # There should only be one geojson file because there is only one div type
            geojson_files = [
                f for f in os.listdir(temp_dir) if f.endswith(".geojson")
            ]
            self.assertEqual(len(geojson_files), 1)
            self.assertTrue(os.path.exists(pm_tile_fp))

    def test_create_pmtiles_file_multiple_div_types(self):
        # Create five  more divisions for the divisionset with different div type
        for _ in range(5):
            div = OrganisationDivisionFactory(
                divisionset=self.divisionset,
                division_type="test_type_2",
            )
            DivisionGeographyFactory(division=div)

        with TemporaryDirectory() as temp_dir:
            pm_tile_fp = self.pmtile_creator.create_pmtile(temp_dir)

            # There should be two geojson files because there are two div types
            geojson_files = [
                f for f in os.listdir(temp_dir) if f.endswith(".geojson")
            ]
            self.assertEqual(len(geojson_files), 2)

            self.assertTrue(os.path.exists(pm_tile_fp))

    def test_create_geojson(self):
        div_type = self.divisionset.divisions.first().division_type

        with TemporaryDirectory() as temp_dir:
            geojson_fp = self.pmtile_creator._create_geojson(temp_dir, div_type)

            self.assertTrue(os.path.exists(geojson_fp))
            with open(geojson_fp) as f:
                geojson = json.load(f)
            self.assertEqual(len(geojson.get("features", [])), 5)

    def test_construct_sql_query_string(self):
        self.maxDiff = None
        divset_id = self.divisionset.id
        div_type = self.divisionset.divisions.first().division_type

        sql_query = self.pmtile_creator._construct_sql_query_string(
            divset_id, div_type
        )

        expected_query = (
            f'SELECT "organisations_divisiongeography"."id", "organisations_divisiongeography"."source", "organisations_divisiongeography"."division_id", "organisations_organisationdivision"."name", "organisations_organisationdivision"."official_identifier", "organisations_divisiongeography"."geography" '
            f'FROM "organisations_divisiongeography" '
            f'INNER JOIN "organisations_organisationdivision" '
            f'ON ("organisations_divisiongeography"."division_id" = "organisations_organisationdivision"."id") '
            f'WHERE ("organisations_organisationdivision"."division_type" = \'{div_type}\' AND "organisations_organisationdivision"."divisionset_id" = {divset_id})'
        )
        self.assertEqual(sql_query, expected_query)
