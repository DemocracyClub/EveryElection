from datetime import datetime, timedelta

from django.test import TestCase
from django.contrib.gis.geos import Point

from elections.tests.factories import (ElectionFactory, )
from elections.models import Election



class TestElectionGeoQueries(TestCase):
    lat = 51.5010089365
    lon = -0.141587600123

    fixtures = ['onspd.json']

    def test_election_for_point(self):
        ElectionFactory(group=None)
        point = Point(self.lon, self.lat)
        qs = Election.public_objects.for_point(point)
        assert qs.count() == 1

    def test_election_for_lat_lng(self):
        ElectionFactory(group=None)
        qs = Election.public_objects.for_lat_lng(
            lat=self.lat, lng=self.lon)
        assert qs.count() == 1

    def test_election_for_postcode(self):
        ElectionFactory(group=None)
        qs = Election.public_objects.for_postcode("SW1A 1AA")
        assert qs.count() == 1

    def test_current_elections(self):
        # This is implicetly current
        ElectionFactory(group=None, poll_open_date=datetime.today())
        # This is implicetly not current
        ElectionFactory(
            group=None, poll_open_date=datetime.today() - timedelta(days=60))
        # This is implicetly not current, but current manually set
        ElectionFactory(
            group=None,
            poll_open_date=datetime.today() - timedelta(days=60),
            current = True
            )
        # This is implicetly current, current manually set to False
        ElectionFactory(
            group=None,
            poll_open_date=datetime.today() - timedelta(days=1),
            current = False
            )
        assert Election.public_objects.current().count() == 2

    def test_future_elections(self):
        ElectionFactory(group=None, poll_open_date=datetime.today())
        ElectionFactory(
            group=None, poll_open_date=datetime.today() - timedelta(days=1))
        assert Election.public_objects.future().count() == 1

    def test_current_elections_for_postcode(self):
        ElectionFactory(group=None, poll_open_date=datetime.today())
        ElectionFactory(
            group=None, poll_open_date=datetime.today(), division_geography=None)
        ElectionFactory(
            group=None, poll_open_date=datetime.today() - timedelta(days=60) )
        assert Election.public_objects.current().for_postcode('SW1A1AA').count() == 1

    def test_public_private_filter(self):
        ElectionFactory(suggested_status='suggested', group=None)
        ElectionFactory(suggested_status='approved', group=None)
        ElectionFactory(suggested_status='rejected', group=None)
        ElectionFactory(suggested_status='deleted', group=None)
        self.assertEqual(1, Election.public_objects.count())
        self.assertEqual(4, Election.private_objects.count())
