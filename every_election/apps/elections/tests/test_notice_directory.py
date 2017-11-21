from django.test import TestCase
from elections.utils import get_notice_directory
from elections.utils import ElectionBuilder
from organisations.models import Organisation, OrganisationDivision


class TestCreateIds(TestCase):

    def setUp(self):
        org = Organisation.objects.create(
            official_identifier='TEST1',
            organisation_type='local-authority',
            official_name="Test Council",
            gss="X00000001",
            slug="test",
            territory_code="ENG",
            election_name="Test Council Local Elections",
        )
        org_div_1 = OrganisationDivision.objects.create(
            organisation=org,
            name="Test Div 1",
            slug="test-div"
        )
        org_div_2 = OrganisationDivision.objects.create(
            organisation=org,
            name="Test Div 2",
            slug="test-div-2"
        )

        self.election = \
            ElectionBuilder('local', '2017-06-08')\
                .build_election_group()

        self.organisation =\
            ElectionBuilder('local', '2017-06-08')\
                .with_organisation(org)\
                .build_organisation_group(None)

        self.ballot1 =\
            ElectionBuilder('local', '2017-06-08')\
                .with_organisation(org)\
                .with_division(org_div_1)\
                .build_ballot(None)

        self.ballot2 =\
            ElectionBuilder('local', '2017-06-08')\
                .with_organisation(org)\
                .with_division(org_div_2)\
                .build_ballot(None)

    def test_one_ballot_with_org(self):
        folder = get_notice_directory([
            self.election,
            self.organisation,
            self.ballot1,
        ])
        self.assertEqual(self.ballot1.election_id, folder)

    def test_one_ballot_no_org(self):
        folder = get_notice_directory([
            self.election,
            self.ballot1,
        ])
        self.assertEqual(self.ballot1.election_id, folder)

    def test_two_ballots_with_org(self):
        folder = get_notice_directory([
            self.election,
            self.organisation,
            self.ballot1,
            self.ballot2,
        ])
        self.assertEqual(self.organisation.election_id, folder)

    def test_two_ballots_no_org(self):
        folder = get_notice_directory([
            self.election,
            self.ballot1,
            self.ballot2,
        ])
        self.assertEqual(self.election.election_id, folder)

    def test_group_only(self):
        folder = get_notice_directory([
            self.election,
            self.organisation,
        ])
        self.assertEqual(self.organisation.election_id, folder)

    def test_invalid_empty(self):
        with self.assertRaises(ValueError):
            get_notice_directory([])

    def test_invalid_two_ballots_no_groups(self):
        with self.assertRaises(ValueError):
            get_notice_directory([
                self.ballot1,
                self.ballot2,
            ])
