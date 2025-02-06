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

        legislation_names = set(legislation_names)
        boundary_names = set(boundary_names)

        missing_from_leg = sorted(boundary_names - legislation_names)
        map = {}
        for name in sorted(legislation_names):
            if name not in boundary_names:
                self.stdout.write(
                    inspect.cleandoc(
                        f"""Legislation is expecting a division called
                    \t{name}
                    but that doesn't exist in the boundary data
                    Might it be one of these?
                    """
                    )
                )
                for i, missing_name in enumerate(missing_from_leg, start=1):
                    self.stdout.write(f"\t {i}. {missing_name}")
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
                    self.stdout.write(
                        f"Asserting that {name} is the same as {matched_name}"
                    )
                    map[matched_name] = name
        return map

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
