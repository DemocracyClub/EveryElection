import contextlib
from datetime import date, timedelta
from datetime import timezone as dt_timezone
from unittest.mock import PropertyMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone as dj_timezone
from elections.models import (
    DEFAULT_STATUS,
    ByElectionReason,
    Election,
    ElectionCancellationReason,
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

        # All timetable fields should be populated on the ballot
        self.assertIsNotNone(ballot.notice_of_election_deadline)
        self.assertIsNotNone(ballot.close_of_nominations)
        self.assertIsNotNone(ballot.sopn_publish_deadline)
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

        self.assertIsNotNone(ballot.notice_of_election_deadline)
        self.assertIsNotNone(ballot.close_of_nominations)
        self.assertIsNotNone(ballot.sopn_publish_deadline)
        self.assertIsNotNone(ballot.registration_deadline)
        self.assertIsNotNone(ballot.postal_vote_application_deadline)

        # VAC deadline should be none on the ballot
        self.assertIsNone(ballot.vac_application_deadline)

        # Timetable fields should all be none on the parent groups
        self.assert_timetable_fields_all_none(election_group)
        self.assert_timetable_fields_all_none(org_group)

    def test_nothern_ireland_ballot(self):
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
            requires_voter_id="EFA-2002",
        )
        ballot.save()

        ballot.refresh_from_db()
        election_group.refresh_from_db()
        org_group.refresh_from_db()

        self.assertIsNotNone(ballot.notice_of_election_deadline)
        self.assertIsNotNone(ballot.close_of_nominations)
        self.assertIsNotNone(ballot.sopn_publish_deadline)
        self.assertIsNotNone(ballot.registration_deadline)
        self.assertIsNotNone(ballot.postal_vote_application_deadline)

        # VAC deadline should be none on the ballot
        # although ID is required in NI
        # VACs are GB-only
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

        # notice_of_election_deadline is optional for referenda
        self.assertIsNone(ballot.notice_of_election_deadline)
        # There is no nominations or SOPN for referenda
        self.assertIsNone(ballot.close_of_nominations)
        self.assertIsNone(ballot.sopn_publish_deadline)

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


class TestCleanMethod(TestCase):
    """
    Tests for Election.clean() validation method
    """

    POLL_DATE = date(2024, 5, 2)

    def _make_ballot(self, **kwargs):
        defaults = {
            "election_id": f"local.test.test-div.{self.POLL_DATE}",
            "election_title": "Test ballot",
            "election_type": ElectionTypeFactory(election_type="local"),
            "poll_open_date": self.POLL_DATE,
            "group_type": None,
        }
        defaults.update(kwargs)
        return Election(**defaults)

    def _make_group(self, group_type="election", **kwargs):
        defaults = {
            "election_id": f"local.{self.POLL_DATE}",
            "election_title": "Local elections",
            "election_type": ElectionTypeFactory(election_type="local"),
            "poll_open_date": self.POLL_DATE,
            "group_type": group_type,
        }
        defaults.update(kwargs)
        return Election(**defaults)

    # --- cancellation rules ---

    def test_group_cannot_be_cancelled(self):
        group = self._make_group(cancelled=True)
        with self.assertRaisesRegex(
            ValidationError,
            "Can't set a group to cancelled",
        ):
            group.clean()

    def test_ballot_can_be_cancelled(self):
        ballot = self._make_ballot(cancelled=True, poll_open_date=None)
        # should not raise
        ballot.clean()

    def test_cancellation_notice_requires_cancelled(self):
        ballot = self._make_ballot(cancelled=False, poll_open_date=None)
        with (
            patch.object(
                type(ballot),
                "cancellation_notice",
                new_callable=PropertyMock,
                return_value=object(),  # truthy stand-in for a Document
            ),
            self.assertRaisesRegex(
                ValidationError,
                "Only a cancelled election can have a cancellation notice",
            ),
        ):
            ballot.clean()

    def test_cancellation_reason_requires_cancelled(self):
        ballot = self._make_ballot(
            cancelled=False,
            cancellation_reason=ElectionCancellationReason.NO_CANDIDATES,
        )
        with self.assertRaisesRegex(
            ValidationError,
            "Only a cancelled election can have a cancellation reason",
        ):
            ballot.clean()

    def test_cancelled_ballot_with_reason_is_valid(self):
        ballot = self._make_ballot(
            cancelled=True,
            cancellation_reason=ElectionCancellationReason.NO_CANDIDATES,
            poll_open_date=None,
        )
        # should not raise
        ballot.clean()

    # --- by_election_reason rules ---

    def test_by_election_reason_requires_by_election_id(self):
        ballot = self._make_ballot(
            election_id=f"local.test.test-div.{self.POLL_DATE}",
            by_election_reason=ByElectionReason.RESIGNATION,
        )
        with self.assertRaisesRegex(
            ValidationError,
            "Only a by election can have a by_election_reason",
        ):
            ballot.clean()

    def test_by_election_reason_allowed_on_by_election(self):
        ballot = self._make_ballot(
            election_id=f"local.test.test-div.by.{self.POLL_DATE}",
            by_election_reason=ByElectionReason.RESIGNATION,
            poll_open_date=None,
        )
        # should not raise
        ballot.clean()

    def test_not_applicable_reason_allowed_on_non_by_election(self):
        ballot = self._make_ballot(
            by_election_reason=ByElectionReason.NOT_APPLICABLE,
            poll_open_date=None,
        )
        # should not raise
        ballot.clean()

    # --- timetable field presence rules ---

    def test_timetable_field_required_raises(self):
        ballot = self._make_ballot()
        ballot.notice_of_election_deadline = self.POLL_DATE - timedelta(days=25)
        ballot.close_of_nominations = self.POLL_DATE - timedelta(days=19)
        ballot.sopn_publish_deadline = self.POLL_DATE - timedelta(days=19)
        ballot.postal_vote_application_deadline = self.POLL_DATE - timedelta(
            days=11
        )

        ballot.registration_deadline = None

        with self.assertRaisesRegex(
            ValidationError, "registration_deadline is required"
        ):
            ballot.clean()

    def test_timetable_field_set_on_group_raises(self):
        group = self._make_group()
        group.registration_deadline = self.POLL_DATE - timedelta(days=11)
        with self.assertRaisesRegex(
            ValidationError,
            "registration_deadline should not be set for this election",
        ):
            group.clean()

    def test_timetable_field_set_without_poll_date_raises(self):
        ballot = self._make_ballot(poll_open_date=None)
        ballot.registration_deadline = date(2024, 4, 21)
        with self.assertRaisesRegex(
            ValidationError,
            "registration_deadline should not be set for this election",
        ):
            ballot.clean()

    # --- timetable field date range rules ---

    def test_timetable_field_after_poll_date_raises(self):
        ballot = self._make_ballot()
        ballot.notice_of_election_deadline = self.POLL_DATE - timedelta(days=25)
        ballot.close_of_nominations = self.POLL_DATE - timedelta(days=19)
        ballot.sopn_publish_deadline = self.POLL_DATE - timedelta(days=19)
        ballot.registration_deadline = self.POLL_DATE - timedelta(days=11)
        ballot.postal_vote_application_deadline = self.POLL_DATE + timedelta(
            days=1
        )  # after poll
        with self.assertRaisesRegex(
            ValidationError,
            "postal_vote_application_deadline must be before poll_open_date",
        ):
            ballot.clean()

    def test_timetable_field_too_far_before_poll_date_raises(self):
        ballot = self._make_ballot()
        ballot.notice_of_election_deadline = self.POLL_DATE - timedelta(
            days=51
        )  # > 50 days
        ballot.close_of_nominations = self.POLL_DATE - timedelta(days=19)
        ballot.sopn_publish_deadline = self.POLL_DATE - timedelta(days=19)
        ballot.registration_deadline = self.POLL_DATE - timedelta(days=11)
        ballot.postal_vote_application_deadline = self.POLL_DATE - timedelta(
            days=11
        )
        with self.assertRaisesRegex(
            ValidationError,
            "notice_of_election_deadline must be within 50 days of poll_open_date",
        ):
            ballot.clean()

    def test_valid_ballot_with_timetable_fields_passes(self):
        ballot = self._make_ballot()
        ballot.notice_of_election_deadline = self.POLL_DATE - timedelta(days=25)
        ballot.close_of_nominations = self.POLL_DATE - timedelta(days=19)
        ballot.sopn_publish_deadline = self.POLL_DATE - timedelta(days=19)
        ballot.registration_deadline = self.POLL_DATE - timedelta(days=11)
        ballot.postal_vote_application_deadline = self.POLL_DATE - timedelta(
            days=11
        )
        # should not raise
        ballot.clean()

    def test_provisional_ballot_passes_without_timetable_fields(self):
        ballot = self._make_ballot(poll_open_date=None)
        # should not raise
        ballot.clean()
