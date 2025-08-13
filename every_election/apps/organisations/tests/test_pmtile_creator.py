import json
import os
from tempfile import TemporaryDirectory

from django.test import TransactionTestCase
from factories import (
    DivisionGeographyFactory,
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
)
from organisations.pmtile_creator import PMtileCreator


class TestPMtilesCreator(TransactionTestCase):
    def setUp(self):
        self.divisionset = OrganisationDivisionSetFactory()
        for _ in range(5):  # Create five divisions for the divisionset
            div = OrganisationDivisionFactory(divisionset=self.divisionset)
            DivisionGeographyFactory(division=div)
        self.pmtile_creator = PMtileCreator(self.divisionset)

    def test_create_pmtile(self):
        with TemporaryDirectory() as temp_dir:
            pm_tile_fp = self.pmtile_creator.create_pmtile(temp_dir)
            self.assertTrue(os.path.exists(pm_tile_fp))

    def test_create_geojson(self):
        with TemporaryDirectory() as temp_dir:
            geojson_fp = self.pmtile_creator.create_geojson(temp_dir)
            self.assertTrue(os.path.exists(geojson_fp))
            with open(geojson_fp) as f:
                geojson = json.load(f)
            self.assertEqual(len(geojson.get("features", [])), 5)

    def test_construct_sql_query(self):
        divset_id = self.divisionset.id
        sql_query = self.pmtile_creator.construct_sql_query(divset_id)

        expected_query = (
            f'SELECT "organisations_divisiongeography"."id", "organisations_divisiongeography"."geography", "organisations_divisiongeography"."source", "organisations_divisiongeography"."division_id", "organisations_organisationdivision"."name" '
            f'FROM "organisations_divisiongeography" '
            f'INNER JOIN "organisations_organisationdivision" '
            f'ON ("organisations_divisiongeography"."division_id" = "organisations_organisationdivision"."id") '
            f'WHERE "organisations_organisationdivision"."divisionset_id" = {divset_id}'
        )
        self.assertEqual(sql_query, expected_query)
