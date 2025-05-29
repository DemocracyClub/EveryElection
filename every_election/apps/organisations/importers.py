import inspect
import json
import sys
from difflib import ndiff

from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.db import transaction
from organisations.models import (
    DivisionGeography,
    OrganisationDivision,
    OrganisationDivisionSet,
)
from storage.shapefile import pre_process_layer


class DiffException(Exception):
    def __init__(self, message, diff):
        super().__init__(message)
        self.diff = diff


class MapCreationNeededException(Exception): ...


class DivisionSetGeographyImporter:
    def __init__(
        self,
        data,
        division_set,
        name_column="name",
        name_map={},
        srid=27700,
        source="unknown",
        stdout=None,
    ):
        if not isinstance(data, DataSource):
            error = "param 'data' must be an instance of django.contrib.gis.gdal.DataSource"
            raise TypeError(error)
        if len(data) != 1:
            raise ValueError("Expected 1 layer, found %i" % (len(data)))
        self.data = data[0]

        self.name_column = name_column
        self.source = source

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

        if not stdout:
            stdout = sys.stdout
        self.stdout = stdout

    def get_name(self, division):
        name = division[self.name_column].value
        if name in self.name_map:
            return self.name_map[name]
        return name

    def make_name_map(self, legislation_names, boundary_names):
        if settings.IN_TESTING:
            return None

        # We want to remove common suffixes from the boundary names before comparing to legislation names,
        # but we want to use the original names in the name map so we build a stripped-orig mapping
        stripped_to_original = self.make_stripped_suffixes_map(boundary_names)

        # We start the name_map by adding all the names that had a suffix stripped successfully
        name_map = {
            orig: stripped
            for stripped, orig in stripped_to_original.items()
            if stripped != orig
        }

        # Then we compare the legislation names to stripped names, if any don't match we prompt the user
        legislation_names = set(legislation_names)
        stripped_boundary_names = set(stripped_to_original.keys())

        missing_from_leg = sorted(stripped_boundary_names - legislation_names)

        for leg_name in sorted(legislation_names):
            if leg_name not in stripped_boundary_names:
                self.stdout.write(
                    inspect.cleandoc(
                        f"""Legislation is expecting a division called
                    \t{leg_name}
                    but that doesn't exist in the boundary data
                    Might it be one of these?
                    """
                    )
                )
                for i, missing_name in enumerate(missing_from_leg, start=1):
                    self.stdout.write(
                        f"\t {i}. {stripped_to_original[missing_name]}"
                    )
                match = None
                while not match:
                    match = input(
                        "Pick a number to match or enter 's' to skip: "
                    )

                    if match:
                        if match == "s":
                            break
                        match = int(match)

                if match != "s":
                    matched_name = missing_from_leg.pop(match - 1)
                    original_name = stripped_to_original[matched_name]
                    self.stdout.write(
                        f"Asserting that {leg_name} is the same as {original_name}"
                    )
                    name_map[original_name] = leg_name
        return name_map

    def make_stripped_suffixes_map(self, boundary_names):
        """
        Creates a mapping from boundary names with common suffixes removed to their original names.
        """
        stripped_to_original = {}
        for name in boundary_names:
            stripped = self.remove_common_suffixes(name)
            stripped_to_original[stripped] = name
        return stripped_to_original

    def remove_common_suffixes(self, name):
        suffixes = [" Electoral Division", " ED", " Division", " Ward"]
        suffixes = suffixes + [s.lower() for s in suffixes]

        for suffix in suffixes:
            name = name.removesuffix(suffix)

        return name

    def check_names(self):
        legislation_names = sorted(
            [div.name for div in self.div_set.divisions.all()]
        )
        boundary_names = sorted([self.get_name(div) for div in self.data])

        if len(legislation_names) != len(boundary_names):
            raise ValueError(
                "Expected %i boundaries in input file, found %i"
                % (len(legislation_names), len(boundary_names))
            )
        if legislation_names != boundary_names:
            map_data = self.make_name_map(legislation_names, boundary_names)
            if map_data:
                self.stdout.write(
                    "\nYou need to save this file as `name_map.json`:"
                )
                self.stdout.write(json.dumps(map_data, indent=4))
                raise MapCreationNeededException()
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
                divisionset=self.div_set, name=name
            )
            div_geogs.append(
                DivisionGeography(
                    division=division,
                    geography=feature.multipolygon,
                    source=self.source,
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
