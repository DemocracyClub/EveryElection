from difflib import ndiff

from django.contrib.gis.gdal import DataSource
from django.db import transaction

from .models import (
    OrganisationDivisionSet,
    OrganisationDivision,
    DivisionGeography,
)
from storage.shapefile import pre_process_layer


class DiffException(Exception):

    def __init__(self, message, diff):
        super().__init__(message)
        self.diff = diff


class DivisionSetGeographyImporter:

    def __init__(self, data, division_set, name_column='name', name_map={}, srid=27700):
        if not isinstance(data, DataSource):
            error = "param 'data' must be an instance of django.contrib.gis.gdal.DataSource"
            raise TypeError(error)
        if len(data) != 1:
            raise ValueError("Expected 1 layer, found %i" % (len(data)))
        self.data = data[0]

        self.name_column = name_column

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

    def get_name(self, division):
        name = division[self.name_column].value
        if name in self.name_map:
            return self.name_map[name]
        return name

    def check_names(self):
        legislation_names = sorted([div.name for div in self.div_set.divisions.all()])
        boundary_names = sorted([self.get_name(div) for div in self.data])

        if len(legislation_names) != len(boundary_names):
            raise ValueError("Expected %i boundaries in input file, found %i"\
                % (len(legislation_names), len(boundary_names)))
        if legislation_names != boundary_names:
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
                divisionset=self.div_set, name=name)
            div_geogs.append(
                DivisionGeography(
                    division=division,
                    organisation=None,
                    geography=feature.multipolygon
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
