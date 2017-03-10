from django.test import TestCase

from elections.tests.factories import (ElectionFactory, )

class TestElectionFactories(TestCase):
    def test_election_factory(self):
        e = ElectionFactory(election_id="local.place-name-0.2017-03-23")
        assert e.election_id == "local.place-name-0.2017-03-23"
