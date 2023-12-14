import datetime

from django.test import TestCase
from elections.sync_helper import ElectionSyncer
from elections.tests.factories import ElectedRoleFactory, ElectionFactory
from organisations.models import Organisation
from organisations.tests.factories import OrganisationFactory


class TestSyncElectionsHelper(TestCase):
    def test_since(self):
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
        role = ElectedRoleFactory()
        helper = ElectionSyncer()
        self.assertDictEqual(helper.ELECTED_ROLE_CACHE, {})
        self.assertEqual(
            helper.get_elected_role("Councillor").elected_title,
            role.elected_title,
        )
        self.assertDictEqual(helper.ELECTED_ROLE_CACHE, {"Councillor": role})

    def test_get_organisation(self):
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
