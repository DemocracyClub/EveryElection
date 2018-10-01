from django.test import TestCase
from elections.models import Election
from elections.utils import ElectionBuilder
from .base_tests import BaseElectionCreatorMixIn


class TestElectionModel(BaseElectionCreatorMixIn, TestCase):

    def setUp(self):
        super().setUp()
        Election.private_objects.all().delete()
        self.parent_election = ElectionBuilder('local', '2017-06-08')\
                .build_election_group()
        self.child_election = ElectionBuilder('local', '2017-06-08')\
                .with_organisation(self.org1)\
                .build_organisation_group(self.parent_election)

    def test_recursive_save(self):
        # table should be empty before we start
        self.assertEqual(0, Election.private_objects.count())

        # saving the child record should implicitly save the parent record too
        self.child_election.save()
        self.assertEqual(2, Election.private_objects.count())

    def test_transaction_rollback_parent(self):
        # table should be empty before we start
        self.assertEqual(0, Election.private_objects.count())

        # doing this will cause save() to throw a exception
        # if we try to save parent_record
        self.parent_election.organisation_id = "foo"

        try:
            self.child_election.save()
        except ValueError:
            pass

        # the exception should have prevented both the
        # parent and child records from being saved
        self.assertEqual(0, Election.private_objects.count())

    def test_transaction_rollback_child(self):
        # table should be empty before we start
        self.assertEqual(0, Election.private_objects.count())

        # doing this will cause save() to throw a exception
        # if we try to save child_record
        self.child_election.organisation_id = "foo"

        try:
            self.child_election.save()
        except ValueError:
            pass

        # the exception should have prevented both the
        # parent and child records from being saved
        self.assertEqual(0, Election.private_objects.count())
