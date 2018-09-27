from django.contrib.gis.gdal import OGRGeometry
from django.test import TestCase
from organisations.boundaries.helpers import normalize_name_for_matching, overlap_percent


class NormalizeNamesTest(TestCase):

    def test_equal(self):
        self.assertEqual(
            normalize_name_for_matching("St. Helen's Ward"),
            normalize_name_for_matching("St. Helen's")
        )
        self.assertEqual(
            normalize_name_for_matching("St. Helen's ED"),
            normalize_name_for_matching("St. Helen's")
        )
        self.assertEqual(
            normalize_name_for_matching("St. Helens"),
            normalize_name_for_matching("St Helen's")
        )

    def test_not_equal(self):
        self.assertNotEqual(
            normalize_name_for_matching("St. Helen's North"),
            normalize_name_for_matching("St. Helen's South")
        )
        self.assertNotEqual(
            normalize_name_for_matching("foo"),
            normalize_name_for_matching("bar")
        )
        self.assertNotEqual(
            normalize_name_for_matching("St. Helena"),
            normalize_name_for_matching("St. Helens")
        )


class OverlapPercentTest(TestCase):

    def test_same_area(self):
        self.assertEqual(
            100,
            overlap_percent(
                OGRGeometry('SRID=4326;POLYGON((-1.9506903391078367 51.34241717557178,-1.8875189523890867 51.34241717557178,-1.8875189523890867 51.32354066802566,-1.9506903391078367 51.34241717557178))'),
                OGRGeometry('SRID=4326;POLYGON((-1.9506903391078367 51.34241717557178,-1.8875189523890867 51.34241717557178,-1.8875189523890867 51.32354066802566,-1.9506903391078367 51.34241717557178))'),
            )
        )

    def test_no_overlap(self):
        self.assertEqual(
            0,
            overlap_percent(
                OGRGeometry('SRID=4326;POLYGON((-1.9506903391078367 51.34241717557178,-1.8875189523890867 51.34241717557178,-1.8875189523890867 51.32354066802566,-1.9506903391078367 51.34241717557178))'),
                OGRGeometry('SRID=4326;POLYGON((-1.9506903391078367 51.34241717557178,-1.8875189523890867 51.32354066802566,-1.9506903391078367 51.32354066802566,-1.9506903391078367 51.34241717557178))'),
            )
        )

    def test_half_inside(self):
        self.assertEqual(
            50,
            round(overlap_percent(
                OGRGeometry('SRID=4326;POLYGON((-1.9506903391078367 51.34241717557178,-1.8875189523890867 51.34241717557178,-1.8875189523890867 51.32354066802566,-1.9506903391078367 51.32354066802566,-1.9506903391078367 51.34241717557178))'),
                OGRGeometry('SRID=4326;POLYGON((-1.9506903391078367 51.34241717557178,-1.8875189523890867 51.32354066802566,-1.9506903391078367 51.32354066802566,-1.9506903391078367 51.34241717557178))'),
            ),0)
        )
