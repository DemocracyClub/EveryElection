import os

from organisations.management.commands.create_pmtile_for_divset import Command
from django.core.management import call_command
from django.test import TestCase, override_settings
from factories import (
    OrganisationDivisionSetFactory,
    OrganisationDivisionFactory,
    DivisionGeographyFactory,
)


class CreatePmTileForDivSetTests(TestCase):
    def setUp(self):
        # Set up any necessary test data or environment here
        self.divisionset = OrganisationDivisionSetFactory()
        for _ in range(5):  # Create five divisions for the divisionset
            div = OrganisationDivisionFactory(divisionset=self.divisionset)
            DivisionGeographyFactory(division=div)

    # TODO: Either mock everything or do thing a different way, also move this to an integration test file
    def test_create_pmtile_for_divset(self):
        divisionset_id = self.divisionset.id
        # Call the management command
        call_command("create_pmtile_for_divset", divisionset_id)
        # Check if the PMTile file was created
        pmtile_file = f"{divisionset_id}_divisions.pmtiles"
        self.assertTrue(os.path.exists(pmtile_file))
        # Clean up the created PMTile file
        os.remove(pmtile_file)

    # test divset with no divisions, divset not found,
    def test_construct_sql_query(self):
        command = Command()
        sql_query = command.construct_sql_query()
        self.assertIn("organisation_division", sql_query)
        self.assertIn("organisation_division_set", sql_query)
        self.assertIn("division_geography", sql_query)
        self.assertIn("WHERE organisation_division_set.id = %s", sql_query)

    def test_use_private_data_path(self):
        test_path = "/tmp/test_private_data_path"
        os.makedirs(test_path, exist_ok=True)
        with override_settings(PRIVATE_DATA_PATH=test_path):
            command = Command()
            # Ensure the path exists
            self.assertTrue(os.path.exists(command.data_path))
            # Ensure the path is a directory
            self.assertTrue(os.path.isdir(command.data_path))
        # Clean up
        os.rmdir(test_path)
