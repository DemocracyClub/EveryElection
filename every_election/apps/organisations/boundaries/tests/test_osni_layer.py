import json
import mock
from django.contrib.gis.geos import MultiPolygon
from django.test import TestCase
from organisations.boundaries.osni import OsniLayer


fake_data = json.dumps({
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "area_name": "Antrim and Newtownabbey",
        "foo": "bar",
        "code": "N09000001",
        "OBJECTID": 1
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [-7.14111328125, 54.559322587438636],
            [-6.9873046875, 54.559322587438636],
            [-6.9873046875, 54.63092808215077],
            [-7.14111328125, 54.63092808215077],
            [-7.14111328125, 54.559322587438636]
          ]
        ]
      }
    }, {
      "type": "Feature",
      "properties": {
        "area_name": "Armagh, Banbridge and Craigavon",
        "foo": "baz",
        "code": "N09000002",
        "OBJECTID": 2
      },
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [
          [
            [
              [-7.14111328125, 54.559322587438636],
              [-6.9873046875, 54.559322587438636],
              [-6.9873046875, 54.63092808215077],
              [-7.14111328125, 54.63092808215077],
              [-7.14111328125, 54.559322587438636]
            ]
          ]
        ]
      }
    }
  ]
})


class OsniLayerTest(TestCase):

    @mock.patch(
        'organisations.boundaries.osni.OsniLayer.get_data_from_url',
        lambda a, b: fake_data
    )
    def test_with_gss(self):
        layer = OsniLayer('foo.bar/baz', 'code', 'area_name')
        self.assertEqual(2, len(layer.features))
        for feature in layer.features:
            self.assertTrue('gss' in feature)
            self.assertIsInstance(feature['geometry'], MultiPolygon)

    @mock.patch(
        'organisations.boundaries.osni.OsniLayer.get_data_from_url',
        lambda a, b: fake_data
    )
    def test_without_gss(self):
        layer = OsniLayer('foo.bar/baz', None, 'area_name')
        self.assertEqual(2, len(layer.features))
        for feature in layer.features:
            self.assertTrue('gss' not in feature)
            self.assertIsInstance(feature['geometry'], MultiPolygon)
