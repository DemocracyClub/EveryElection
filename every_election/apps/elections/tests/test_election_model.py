import contextlib
from datetime import timezone as dt_timezone
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone as dj_timezone
from elections.models import (
    DEFAULT_STATUS,
    Election,
    ModerationHistory,
    ModerationStatuses,
)
from elections.tests.factories import ElectionFactory, ElectionTypeFactory
from elections.utils import ElectionBuilder
from freezegun import freeze_time
from organisations.tests.factories import (
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
    OrganisationFactory,
)

from .base_tests import BaseElectionCreatorMixIn


class TestElectionModel(BaseElectionCreatorMixIn, TestCase):
    def setUp(self):
        super().setUp()
        Election.private_objects.all().delete()
        self.election_group = ElectionBuilder(
            "local", "2017-06-08"
        ).build_election_group()
        self.org_group = (
            ElectionBuilder("local", "2017-06-08")
            .with_organisation(self.org1)
            .build_organisation_group(self.election_group)
        )
        self.ballot = (
            ElectionBuilder("local", "2017-06-08")
            .with_organisation(self.org1)
            .with_division(self.org_div_1)
            .build_ballot(self.org_group)
        )
        self.testshire_org_group = (
            ElectionBuilder("local", "2017-06-08")
            .with_organisation(self.testshire_org)
            .build_organisation_group(self.election_group)
        )

        self.testshire_ballot = (
            ElectionBuilder("local", "2017-06-08")
            .with_organisation(self.testshire_org)
            .with_division(self.testshire_div)
            .build_ballot(self.testshire_org_group)
        )

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
        with self.assertNumQueries(25):
            self.ballot.save()

        # saving the child record should implicitly save the parent records too
        self.assertEqual(3, Election.private_objects.count())

    def test_transaction_rollback_parent(self):
        # table should be empty before we start
        self.assertEqual(0, Election.private_objects.count())

        # doing this will cause save() to throw a exception
        # if we try to save parent_record
        self.election_group.organisation_id = "foo"

        with contextlib.suppress(ValueError):
            self.org_group.save()

        # the exception should have prevented both the
        # parent and child records from being saved
        self.assertEqual(0, Election.private_objects.count())

    def test_transaction_rollback_child(self):
        # table should be empty before we start
        self.assertEqual(0, Election.private_objects.count())

        # doing this will cause save() to throw a exception
        # if we try to save child_record
        self.org_group.organisation_id = "foo"

        with contextlib.suppress(ValueError):
            self.org_group.save()

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
        self.election_group.source = "some bloke down the pub told me"
        self.election_group.save()
        self.assertEqual(1, ModerationHistory.objects.count())

    def test_save_with_status(self):
        self.election_group.save()
        self.assertEqual(self.election_group.current_status, DEFAULT_STATUS)

        self.election_group.save(status=ModerationStatuses.approved.value)
        self.assertEqual(
            self.election_group.current_status,
            ModerationStatuses.approved.value,
        )

    def test_get_ballots(self):
        for election in [
            self.election_group,
            self.testshire_org_group,
            self.testshire_ballot,
            self.org_group,
            self.ballot,
        ]:
            election.save(status=ModerationStatuses.approved.value)

        self.assertEqual(
            len(self.org_group.get_ballots()),
            1,
        )
        self.assertEqual(len(self.election_group.get_ballots()), 2)

    def test_seat_counts(self):
        for election in [
            self.election_group,
            self.testshire_org_group,
            self.org_group,
        ]:
            election.save(status=ModerationStatuses.approved.value)

        self.testshire_ballot.seats_contested = 2
        self.testshire_ballot.save(status=ModerationStatuses.approved.value)

        self.ballot.cancelled = True
        self.ballot.seats_contested = 4
        self.ballot.save(status=ModerationStatuses.approved.value)

        self.assertEqual(self.testshire_ballot.group_seats_contested, 2)
        self.assertEqual(self.testshire_ballot.group_seats_cancelled, 0)

        self.assertEqual(self.ballot.group_seats_contested, 0)
        self.assertEqual(self.ballot.group_seats_cancelled, 4)

        self.assertEqual(self.testshire_org_group.group_seats_contested, 2)
        self.assertEqual(self.testshire_org_group.group_seats_cancelled, 0)

        self.assertEqual(self.org_group.group_seats_contested, 0)
        self.assertEqual(self.org_group.group_seats_cancelled, 4)

        self.assertEqual(self.election_group.group_seats_contested, 2)
        self.assertEqual(self.election_group.group_seats_cancelled, 4)

    def test_get_admin_url(self):
        election = Election(pk=2021)
        self.assertEqual(
            election.get_admin_url(),
            f"/admin/elections/election/{election.pk}/change/",
        )

    def test_get_children(self):
        for election in [
            self.election_group,
            self.testshire_org_group,
            self.testshire_ballot,
            self.org_group,
            self.ballot,
        ]:
            election.save(status=ModerationStatuses.approved.value)
        self.testshire_ballot.save(status=ModerationStatuses.deleted.value)

        self.assertEqual(
            len(self.org_group.get_children("public_objects").all()),
            1,
        )
        self.assertEqual(
            len(self.election_group.get_children("public_objects").all()), 2
        )

        self.assertEqual(
            len(self.testshire_org_group.get_children("private_objects").all()),
            1,
        )
        self.assertEqual(
            len(self.testshire_org_group.get_children("public_objects").all()),
            0,
        )

    def test_get_descendents_exclusive(self):
        for election in [
            self.election_group,
            self.testshire_org_group,
            self.testshire_ballot,
            self.org_group,
            self.ballot,
        ]:
            election.save(status=ModerationStatuses.approved.value)
        self.testshire_ballot.save(status=ModerationStatuses.deleted.value)

        with self.assertNumQueries(1):
            self.assertEqual(
                len(self.org_group.get_descendents("public_objects")),
                1,
            )
        with self.assertNumQueries(1):
            self.assertEqual(
                len(self.election_group.get_descendents("private_objects")), 4
            )
        with self.assertNumQueries(1):
            self.assertEqual(
                len(self.election_group.get_descendents("public_objects")), 3
            )

    def test_get_descendents_inclusive(self):
        for election in [
            self.election_group,
            self.testshire_org_group,
            self.testshire_ballot,
            self.org_group,
            self.ballot,
        ]:
            election.save(status=ModerationStatuses.approved.value)
        self.testshire_ballot.save(status=ModerationStatuses.deleted.value)

        with self.assertNumQueries(1):
            self.assertEqual(
                len(
                    self.org_group.get_descendents(
                        "public_objects", inclusive=True
                    )
                ),
                2,
            )

        with self.assertNumQueries(1):
            self.assertEqual(
                len(
                    self.election_group.get_descendents(
                        "private_objects", inclusive=True
                    )
                ),
                5,
            )

        with self.assertNumQueries(1):
            self.assertEqual(
                len(
                    self.election_group.get_descendents(
                        "public_objects", inclusive=True
                    )
                ),
                4,
            )

    def test_requires_voter_id_empty(self):
        self.ballot.requires_voter_id = ""
        self.ballot.save()
        assert self.ballot.requires_voter_id is None

    def test_ballot_push_event_true(self):
        test_cases = [
            [ModerationStatuses.approved.value, 1],
            [ModerationStatuses.deleted.value, 1],
            [ModerationStatuses.suggested.value, 0],
            [ModerationStatuses.deleted.value, 0],
        ]
        for status, expected_calls in test_cases:
            with (
                patch("elections.models.send_event") as send_event_mock,
            ):
                self.ballot.save(status=status)
                assert send_event_mock.call_count == expected_calls

    def test_ballot_push_event_false(self):
        test_cases = [
            ModerationStatuses.approved.value,
            ModerationStatuses.deleted.value,
            ModerationStatuses.suggested.value,
            ModerationStatuses.deleted.value,
        ]
        for status in test_cases:
            with (
                patch("elections.models.send_event") as send_event_mock,
            ):
                self.ballot.save(status=status, push_event=False)
                assert send_event_mock.call_count == 0


class TestModified(TestCase):
    def test_update_changes_modified(self):
        election = ElectionFactory()

        future = dj_timezone.datetime(
            2022, 5, 5, 12, 0, 0, tzinfo=dt_timezone.utc
        )
        with freeze_time("2022-5-5 12:00:00"):
            self.assertNotEqual(election.modified, future)
            Election.private_objects.update()
            election.refresh_from_db()
            self.assertEqual(election.modified, future)


class TestTimetableFields(TestCase):
    POLL_DATE = "2024-05-02"

    def assert_timetable_fields_all_none(self, election):
        for field in Election.TIMETABLE_FIELDS:
            self.assertIsNone(getattr(election, field))

    def test_requires_id(self):
        org = OrganisationFactory(territory_code="ENG")
        election_type = ElectionTypeFactory(election_type="local")
        div_set = OrganisationDivisionSetFactory(organisation=org)
        div = OrganisationDivisionFactory(divisionset=div_set)

        election_group = Election(
            election_id=f"local.{self.POLL_DATE}",
            election_title="Local elections",
            election_type=election_type,
            poll_open_date=self.POLL_DATE,
            group_type="election",
        )
        election_group.save()

        org_group = Election(
            election_id=f"local.{org.slug}.{self.POLL_DATE}",
            election_title=f"Local elections - {org.official_name}",
            election_type=election_type,
            organisation=org,
            poll_open_date=self.POLL_DATE,
            group=election_group,
            group_type="organisation",
        )
        org_group.save()

        ballot = Election(
            election_id=f"local.{org.slug}.{div.slug}.{self.POLL_DATE}",
            election_title=f"Local elections - {org.official_name} - {div.name}",
            election_type=election_type,
            organisation=org,
            division=div,
            poll_open_date=self.POLL_DATE,
            group=org_group,
            group_type=None,
            requires_voter_id="EA-2022",
        )
        ballot.save()

        ballot.refresh_from_db()
        election_group.refresh_from_db()
        org_group.refresh_from_db()

        # All 4 timetable fields should be populated on the ballot
        self.assertIsNotNone(ballot.close_of_nominations)
        self.assertIsNotNone(ballot.registration_deadline)
        self.assertIsNotNone(ballot.postal_vote_application_deadline)
        self.assertIsNotNone(ballot.vac_application_deadline)

        # Timetable fields should all be none on the parent groups
        self.assert_timetable_fields_all_none(election_group)
        self.assert_timetable_fields_all_none(org_group)

    def test_no_id_required(self):
        org = OrganisationFactory(territory_code="WLS")
        election_type = ElectionTypeFactory(election_type="local")
        div_set = OrganisationDivisionSetFactory(organisation=org)
        div = OrganisationDivisionFactory(divisionset=div_set)

        election_group = Election(
            election_id=f"local.{self.POLL_DATE}",
            election_title="Local elections",
            election_type=election_type,
            poll_open_date=self.POLL_DATE,
            group_type="election",
        )
        election_group.save()

        org_group = Election(
            election_id=f"local.{org.slug}.{self.POLL_DATE}",
            election_title=f"Local elections - {org.official_name}",
            election_type=election_type,
            organisation=org,
            poll_open_date=self.POLL_DATE,
            group=election_group,
            group_type="organisation",
        )
        org_group.save()

        ballot = Election(
            election_id=f"local.{org.slug}.{div.slug}.{self.POLL_DATE}",
            election_title=f"Local elections - {org.official_name} - {div.name}",
            election_type=election_type,
            organisation=org,
            division=div,
            poll_open_date=self.POLL_DATE,
            group=org_group,
            group_type=None,
            requires_voter_id=None,
        )
        ballot.save()

        ballot.refresh_from_db()
        election_group.refresh_from_db()
        org_group.refresh_from_db()

        self.assertIsNotNone(ballot.close_of_nominations)
        self.assertIsNotNone(ballot.registration_deadline)
        self.assertIsNotNone(ballot.postal_vote_application_deadline)

        # VAC deadline should be none on the ballot
        self.assertIsNone(ballot.vac_application_deadline)

        # Timetable fields should all be none on the parent groups
        self.assert_timetable_fields_all_none(election_group)
        self.assert_timetable_fields_all_none(org_group)

    def test_referendum(self):
        org = OrganisationFactory(territory_code="ENG")
        election_type = ElectionTypeFactory(election_type="ref")
        div_set = OrganisationDivisionSetFactory(organisation=org)
        div = OrganisationDivisionFactory(divisionset=div_set)

        election_group = Election(
            election_id=f"ref.{self.POLL_DATE}",
            election_title="Referendum",
            election_type=election_type,
            poll_open_date=self.POLL_DATE,
            group_type="election",
        )
        election_group.save()

        org_group = Election(
            election_id=f"ref.{org.slug}.{self.POLL_DATE}",
            election_title=f"Referendum - {org.official_name}",
            election_type=election_type,
            organisation=org,
            poll_open_date=self.POLL_DATE,
            group=election_group,
            group_type="organisation",
        )
        org_group.save()

        ballot = Election(
            election_id=f"ref.{org.slug}.{div.slug}.{self.POLL_DATE}",
            election_title=f"Referendum - {org.official_name} - {div.name}",
            election_type=election_type,
            organisation=org,
            division=div,
            poll_open_date=self.POLL_DATE,
            group=org_group,
            group_type=None,
        )
        ballot.save()

        ballot.refresh_from_db()
        election_group.refresh_from_db()
        org_group.refresh_from_db()

        self.assertIsNotNone(ballot.registration_deadline)
        self.assertIsNotNone(ballot.postal_vote_application_deadline)

        # Close of nominations should be none on the ballot
        self.assertIsNone(ballot.close_of_nominations)

        # Timetable fields should all be none on the parent groups
        self.assert_timetable_fields_all_none(election_group)
        self.assert_timetable_fields_all_none(org_group)

    def test_provisional_ballot(self):
        org = OrganisationFactory(territory_code="ENG")
        election_type = ElectionTypeFactory(election_type="local")
        div_set = OrganisationDivisionSetFactory(organisation=org)
        div = OrganisationDivisionFactory(divisionset=div_set)

        election_group = Election(
            tmp_election_id="local.TBD",
            election_title="Local elections",
            election_type=election_type,
            poll_open_date=None,
            group_type="election",
        )
        election_group.save()

        org_group = Election(
            tmp_election_id=f"local.{org.slug}.TBD",
            election_title=f"Local elections - {org.official_name}",
            election_type=election_type,
            organisation=org,
            poll_open_date=None,
            group=election_group,
            group_type="organisation",
        )
        org_group.save()

        ballot = Election(
            tmp_election_id=f"local.{org.slug}.{div.slug}.TBD",
            election_title=f"Local elections - {org.official_name} - {div.name}",
            election_type=election_type,
            organisation=org,
            division=div,
            poll_open_date=None,
            group=org_group,
            group_type=None,
        )
        ballot.save()

        ballot.refresh_from_db()
        election_group.refresh_from_db()
        org_group.refresh_from_db()

        # Timetable fields should all be none on  all election objects
        self.assert_timetable_fields_all_none(ballot)
        self.assert_timetable_fields_all_none(election_group)
        self.assert_timetable_fields_all_none(org_group)
