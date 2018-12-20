from django.test import TestCase
from elections.utils import get_notice_directory
from elections.utils import ElectionBuilder
from .base_tests import BaseElectionCreatorMixIn


class TestCreateIds(BaseElectionCreatorMixIn, TestCase):
    def setUp(self):
        super().setUp()

        self.election = ElectionBuilder("local", "2017-06-08").build_election_group()

        self.organisation = (
            ElectionBuilder("local", "2017-06-08")
            .with_organisation(self.org1)
            .build_organisation_group(None)
        )

        self.ballot1 = (
            ElectionBuilder("local", "2017-06-08")
            .with_organisation(self.org1)
            .with_division(self.org_div_1)
            .build_ballot(None)
        )

        self.ballot2 = (
            ElectionBuilder("local", "2017-06-08")
            .with_organisation(self.org1)
            .with_division(self.org_div_2)
            .build_ballot(None)
        )

    def test_one_ballot_with_org(self):
        folder = get_notice_directory([self.election, self.organisation, self.ballot1])
        self.assertEqual(self.ballot1.election_id, folder)

    def test_one_ballot_no_org(self):
        folder = get_notice_directory([self.election, self.ballot1])
        self.assertEqual(self.ballot1.election_id, folder)

    def test_two_ballots_with_org(self):
        folder = get_notice_directory(
            [self.election, self.organisation, self.ballot1, self.ballot2]
        )
        self.assertEqual(self.organisation.election_id, folder)

    def test_two_ballots_no_org(self):
        folder = get_notice_directory([self.election, self.ballot1, self.ballot2])
        self.assertEqual(self.election.election_id, folder)

    def test_group_only(self):
        folder = get_notice_directory([self.election, self.organisation])
        self.assertEqual(self.organisation.election_id, folder)

    def test_invalid_empty(self):
        with self.assertRaises(ValueError):
            get_notice_directory([])

    def test_invalid_two_ballots_no_groups(self):
        with self.assertRaises(ValueError):
            get_notice_directory([self.ballot1, self.ballot2])
