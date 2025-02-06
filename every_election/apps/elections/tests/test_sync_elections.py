import datetime

from django.test import TestCase
from elections.models import Election, ElectionCancellationReason
from elections.sync_helper import ElectionSyncer
from elections.tests.factories import ElectedRoleFactory, ElectionFactory
from elections.tests.test_election_sync_fixtures import get_local_ballot
from organisations.models import Organisation, OrganisationDivisionSet
from organisations.tests.factories import (
    OrganisationFactory,
)


class TestSyncElectionsHelper(TestCase):
    """
    Tests for the election sync management command.

    """

    def test_since(self):
        """
        Test the date returned from the get_last_modified method.

        If no date is passed in (e.g. if there are no elections in the system) then a date in the
        far past should be returned to ensure we get every possible election in the system.

        """

        helper = ElectionSyncer()
        self.assertEqual(
            helper.get_last_modified(None), datetime.datetime(1832, 6, 7, 0, 0)
        )

        self.assertEqual(
            helper.get_last_modified(since=datetime.datetime(2022, 1, 1, 0, 0)),
            datetime.datetime(2022, 1, 1, 0, 0),
        )

        election = ElectionFactory()

        expected = (
            election.modified - datetime.timedelta(hours=1, minutes=1)
        ).replace(tzinfo=None)

        self.assertEqual(
            helper.get_last_modified(),
            expected,
        )

    def test_get_elected_role(self):
        """
        Test that we can get an elected role and that we cache it

        """
        role = ElectedRoleFactory()
        helper = ElectionSyncer()
        self.assertDictEqual(helper.ELECTED_ROLE_CACHE, {})
        self.assertEqual(
            helper.get_elected_role("Councillor").elected_title,
            role.elected_title,
        )
        self.assertDictEqual(helper.ELECTED_ROLE_CACHE, {"Councillor": role})

    def test_get_organisation(self):
        """
        Test that the election syncer can get an organisation

        """
        org = OrganisationFactory(
            official_identifier="ABC", start_date="2022-01-01"
        )
        helper = ElectionSyncer()

        matched_org = helper.get_organisation(
            {
                "official_identifier": "ABC",
                "start_date": "2022-01-01",
                "end_date": None,
            }
        )
        self.assertEqual(org, matched_org)

    def test_get_organisation_update_end_date(self):
        """
        Test that we can update an organisation's end date when the
        remove API returns an end date

        """
        org: Organisation = OrganisationFactory(
            official_identifier="ABC", start_date="2022-01-01"
        )
        self.assertEqual(org.end_date, None)
        helper = ElectionSyncer()

        helper.get_organisation(
            {
                "official_identifier": "ABC",
                "start_date": "2022-01-01",
                "end_date": "2022-01-02",
            }
        )
        org.refresh_from_db()
        self.assertEqual(org.end_date, datetime.date(2022, 1, 2))


class TestDivisionSetStartAndEndDates(TestCase):
    """
    We need to sync division sets, especially when they start and stop.

    """

    def test_can_set_divisionset_end_date(self):
        helper = ElectionSyncer()

        # First, make an election from the API response
        ballot = get_local_ballot()
        helper.add_single_election(ballot)
        div_set = OrganisationDivisionSet.objects.get(
            **ballot["division"]["divisionset"]
        )
        self.assertIsNone(div_set.end_date)

        # Then, add an end date
        updated_ballot = ballot.copy()
        updated_ballot["division"]["divisionset"]["end_date"] = "2022-05-02"
        helper.add_single_election(updated_ballot)
        div_set.refresh_from_db()
        self.assertEqual(div_set.end_date, datetime.date(2022, 5, 2))

    def test_can_update_divisionset_end_date(self):
        helper = ElectionSyncer()

        # First, make an election from the API response
        ballot = get_local_ballot()
        helper.add_single_election(ballot)
        div_set = OrganisationDivisionSet.objects.get(
            **ballot["division"]["divisionset"]
        )

        # Set an end date
        div_set.end_date = datetime.date(2023, 5, 4)
        div_set.save()

        # Check we set it
        div_set.refresh_from_db()
        self.assertEqual(div_set.end_date, datetime.date(2023, 5, 4))

        # Then, add a new end date via the syncer
        updated_ballot = ballot.copy()
        updated_ballot["division"]["divisionset"]["end_date"] = "2022-05-02"
        helper.add_single_election(updated_ballot)

        # Check it's changed
        div_set.refresh_from_db()
        self.assertEqual(div_set.end_date, datetime.date(2022, 5, 2))

    def test_can_change_start_date(self):
        """
        We see an election a divisionset that doesn't match the start date we expect it to have.

        In this case, we try to match the divisionset to one we already know about.

        If we can't match it, we raise an error.

        If we can, we change the start (and end) date to match the one we've got from the remove data.

        This is needed to cover the case where we have changed the start date. For example, for the 2024/2025 UK
        general election we don't (didn't) know the end date of the previous divisionset until the election was called.

        """
        helper = ElectionSyncer()

        # Get a template ballot
        ballot = get_local_ballot()
        ballot["division"]["divisionset"]["start_date"] = "2022-05-02"

        helper.add_single_election(ballot)
        div_set = OrganisationDivisionSet.objects.get(
            **ballot["division"]["divisionset"]
        )
        self.assertIsNone(div_set.end_date)


class TestElectionSyncerCancelsElection(TestCase):
    def test_election_cancelled(self):
        helper = ElectionSyncer()

        # Get a template ballot
        ballot = get_local_ballot()
        helper.add_single_election(ballot)
        created_election: Election = Election.public_objects.get()
        self.assertEqual(
            created_election.election_id,
            "local.reigate-and-banstead.banstead-village.2022-05-05",
        )
        self.assertFalse(created_election.cancelled)

        ballot["cancelled"] = True
        ballot["cancellation_reason"] = (
            ElectionCancellationReason.CANDIDATE_DEATH
        )
        helper.add_single_election(ballot)
        created_election.refresh_from_db()
        self.assertTrue(created_election.cancelled)
        self.assertEqual(
            created_election.cancellation_reason, "CANDIDATE_DEATH"
        )


class TestElectionSyncerCreatesElection(TestCase):
    def test_election_created(self):
        helper = ElectionSyncer()

        # Change the id
        ballot = get_local_ballot()
        ballot["election_id"] = (
            "local.reigate-and-banstead.banstead-village.2023-05-04"
        )
        ballot["poll_open_date"] = "2023-05-04"

        # Check it doesn't exist
        with self.assertRaises(Election.DoesNotExist):
            Election.private_objects.get(
                election_id="local.reigate-and-banstead.banstead-village.2023-05-04"
            )

        helper.add_single_election(ballot)

        self.assertTrue(
            Election.public_objects.filter(
                election_id="local.reigate-and-banstead.banstead-village.2023-05-04"
            ).exists()
        )

    def test_election_created_and_divset_end_date_updated(self):
        helper = ElectionSyncer()

        # Change the id
        ballot = get_local_ballot()
        ballot["election_id"] = (
            "local.reigate-and-banstead.banstead-village.2023-05-04"
        )
        ballot["poll_open_date"] = "2023-05-04"

        # Check it doesn't exist
        with self.assertRaises(Election.DoesNotExist):
            Election.private_objects.get(
                election_id="local.reigate-and-banstead.banstead-village.2023-05-04"
            )

        # show the divset doesn't have an end date
        div_set = OrganisationDivisionSet.objects.get(
            **ballot["division"]["divisionset"]
        )
        self.assertIsNone(div_set.end_date)

        # Then, add an end date to the ballot
        updated_ballot = ballot.copy()
        updated_ballot["division"]["divisionset"]["end_date"] = "2024-05-02"

        helper.add_single_election(ballot)

        # check the election exists...
        self.assertTrue(
            Election.public_objects.filter(
                election_id="local.reigate-and-banstead.banstead-village.2023-05-04"
            ).exists()
        )

        # ...and the end date is updated
        div_set.refresh_from_db()
        self.assertEqual(div_set.end_date, datetime.date(2024, 5, 2))
