from django.test import TestCase
from elections.utils import get_notice_directory


class IDMakerMock(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


election = IDMakerMock(
    group_type='election',
    is_group_id=True,
    to_id=lambda: "local.election.date")

organisation = IDMakerMock(
    group_type='organisation',
    is_group_id=True,
    to_id=lambda: "local.election.organisation.date")

ballot1 = IDMakerMock(
    group_type='election',
    is_group_id=False,
    to_id=lambda: "local.election.ballot1.date")

ballot2 = IDMakerMock(
    group_type='election',
    is_group_id=False,
    to_id=lambda: "local.election.ballot2.date")


class TestCreateIds(TestCase):

    def test_one_ballot_with_org(self):
        folder = get_notice_directory([
            election,
            organisation,
            ballot1,
        ])
        self.assertEqual(ballot1.to_id(), folder)

    def test_one_ballot_no_org(self):
        folder = get_notice_directory([
            election,
            ballot1,
        ])
        self.assertEqual(ballot1.to_id(), folder)

    def test_two_ballots_with_org(self):
        folder = get_notice_directory([
            election,
            organisation,
            ballot1,
            ballot2,
        ])
        self.assertEqual(organisation.to_id(), folder)

    def test_two_ballots_no_org(self):
        folder = get_notice_directory([
            election,
            ballot1,
            ballot2,
        ])
        self.assertEqual(election.to_id(), folder)

    def test_group_only(self):
        folder = get_notice_directory([
            election,
            organisation,
        ])
        self.assertEqual(organisation.to_id(), folder)

    def test_invalid_empty(self):
        with self.assertRaises(ValueError):
            get_notice_directory([])

    def test_invalid_two_ballots_no_groups(self):
        with self.assertRaises(ValueError):
            get_notice_directory([
                ballot1,
                ballot2,
            ])
