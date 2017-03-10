from datetime import datetime, timedelta

import vcr

from django.test import TestCase
from django.contrib.gis.geos import Point

from elections.tests.factories import (ElectionFactory, )
from elections.models import Election



class TestElectionGeoQueries(TestCase):
    lat = 51.5010089365
    lon = -0.141587600123

    def test_election_for_point(self):
        ElectionFactory(group=None)
        point = Point(self.lon, self.lat)
        qs = Election.objects.for_point(point)
        assert qs.count() == 1

    def test_election_for_lat_lng(self):
        ElectionFactory(group=None)
        qs = Election.objects.for_lat_lng(
            lat=self.lat, lng=self.lon)
        assert qs.count() == 1

    @vcr.use_cassette(
        'fixtures/vcr_cassettes/test_election_for_postcode.yaml')
    def test_election_for_postcode(self):
        ElectionFactory(group=None)
        qs = Election.objects.for_postcode("SW1A 1AA")
        assert qs.count() == 1


    def test_current_elections(self):
        ElectionFactory(group=None, poll_open_date=datetime.today())
        ElectionFactory(
            group=None, poll_open_date=datetime.today() - timedelta(days=60))
        assert Election.objects.current().count() == 1

    def test_future_elections(self):
        ElectionFactory(group=None, poll_open_date=datetime.today())
        ElectionFactory(
            group=None, poll_open_date=datetime.today() - timedelta(days=1))
        assert Election.objects.future().count() == 1

    @vcr.use_cassette(
        'fixtures/vcr_cassettes/test_election_for_postcode.yaml')
    def test_current_elections_for_postcode(self):
        ElectionFactory(group=None, poll_open_date=datetime.today())
        ElectionFactory(
            group=None, poll_open_date=datetime.today(), geography=None)
        ElectionFactory(
            group=None, poll_open_date=datetime.today() - timedelta(days=60) )
        assert Election.objects.current().for_postcode('SW1A1AA').count() == 1
