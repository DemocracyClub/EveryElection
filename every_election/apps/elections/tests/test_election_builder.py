from django.test import TestCase
from elections.utils import ElectionBuilder
from organisations.tests.factories import OrganisationFactory
from .base_tests import BaseElectionCreatorMixIn


class TestElectionBuilder(BaseElectionCreatorMixIn, TestCase):

    def test_eq(self):
        eb1 = ElectionBuilder('local', '2017-06-08')

        eb2 = ElectionBuilder('local', '2017-06-08')\
            .with_source('foo/bar.baz')\
            .with_snooped_election(7)

        # these should be 'equal' because only the meta-data differs
        self.assertEqual(eb1, eb2)

        eb2 = eb2.with_organisation(self.org1)

        # now these objects will build funamentally different elections
        self.assertNotEqual(eb1, eb2)
