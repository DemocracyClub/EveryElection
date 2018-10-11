from django.test import TestCase
from elections.models import Election, ModerationHistory
from elections.utils import ElectionBuilder
from .base_tests import BaseElectionCreatorMixIn


class TestElectionModel(BaseElectionCreatorMixIn, TestCase):

    def setUp(self):
        super().setUp()
        Election.private_objects.all().delete()
        self.election_group = ElectionBuilder('local', '2017-06-08')\
                .build_election_group()
        self.org_group = ElectionBuilder('local', '2017-06-08')\
                .with_organisation(self.org1)\
                .build_organisation_group(self.election_group)
        self.ballot = ElectionBuilder('local', '2017-06-08')\
                .with_organisation(self.org1)\
                .with_division(self.org_div_1)\
                .build_ballot(self.org_group)

    def test_recursive_save_group(self):
        # table should be empty before we start
        self.assertEqual(0, Election.private_objects.count())

        # saving the child record should implicitly save the parent record too
        self.org_group.save()
        self.assertEqual(2, Election.private_objects.count())

    def test_recursive_save_ballot(self):
        # table should be empty before we start
        self.assertEqual(0, Election.private_objects.count())

        # From a performance perspective, saving a ballot and 2 parent groups
        # is the worst-case scenario for database I/O
        # we should monitor this and be aware if this number increases
        with self.assertNumQueries(19):
            self.ballot.save()

        # saving the child record should implicitly save the parent records too
        self.assertEqual(3, Election.private_objects.count())

    def test_transaction_rollback_parent(self):
        # table should be empty before we start
        self.assertEqual(0, Election.private_objects.count())

        # doing this will cause save() to throw a exception
        # if we try to save parent_record
        self.election_group.organisation_id = "foo"

        try:
            self.org_group.save()
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
        self.org_group.organisation_id = "foo"

        try:
            self.org_group.save()
        except ValueError:
            pass

        # the exception should have prevented both the
        # parent and child records from being saved
        self.assertEqual(0, Election.private_objects.count())

    def test_related_object_save(self):
        # table should be empty before we start
        self.assertEqual(0, ModerationHistory.objects.count())

        # the first time we save a record, we should create
        # a corresponding moderation status event
        self.election_group.save()
        self.assertEqual(1, ModerationHistory.objects.count())

        # saving the same record again shouldn't though
        self.election_group.seats_contests = 7
        self.election_group.source = 'some bloke down the pub told me'
        self.election_group.save()
        self.assertEqual(1, ModerationHistory.objects.count())
