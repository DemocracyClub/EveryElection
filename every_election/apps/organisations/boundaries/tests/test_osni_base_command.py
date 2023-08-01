import json

from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase
from organisations.boundaries.management.base import BaseOsniCommand
from organisations.models import DivisionGeography
from organisations.tests.factories import (
    DivisionGeographyFactory,
    OrganisationDivisionFactory,
    OrganisationFactory,
    OrganisationGeographyFactory,
)

fake_record = {
    "geometry": GEOSGeometry(
        json.dumps(
            {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [-7.14111328125, 54.559322587438636],
                            [-6.9873046875, 54.559322587438636],
                            [-6.9873046875, 54.63092808215077],
                            [-7.14111328125, 54.63092808215077],
                            [-7.14111328125, 54.559322587438636],
                        ]
                    ]
                ],
            }
        ),
        srid=4326,
    )
}


class ConcreteOsniCommand(BaseOsniCommand):
    def handle(self, *args, **options):
        pass


class OsniBaseCommandTest(TestCase):
    def test_import_org_geography(self):
        cmd = ConcreteOsniCommand()
        og = OrganisationGeographyFactory(
            organisation=OrganisationFactory(), geography=None, source="unknown"
        )
        cmd.import_org_geography(og, fake_record)
        self.assertEqual(fake_record["geometry"], og.geography)
        self.assertEqual(cmd.source, og.source)

    def test_import_div_geog_exists(self):
        cmd = ConcreteOsniCommand()
        div = OrganisationDivisionFactory()
        DivisionGeographyFactory(division=div, source="unknown")
        cmd.import_div_geography(div, fake_record)
        self.assertEqual(fake_record["geometry"], div.geography.geography)
        self.assertEqual(cmd.source, div.geography.source)

    def test_import_div_doesnt_exist(self):
        cmd = ConcreteOsniCommand()
        div = OrganisationDivisionFactory()
        cmd.import_div_geography(div, fake_record)
        dg = DivisionGeography.objects.all().get(division_id=div.id)
        self.assertEqual(fake_record["geometry"], dg.geography)
        self.assertEqual(cmd.source, dg.source)
