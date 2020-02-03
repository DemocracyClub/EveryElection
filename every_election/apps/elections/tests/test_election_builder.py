from datetime import date
from django.test import TestCase
from elections.models import (
    DEFAULT_STATUS,
    Election,
    ElectedRole,
    ElectionSubType,
    ElectionType,
)
from elections.utils import ElectionBuilder
from election_snooper.models import SnoopedElection
from organisations.models import Organisation, OrganisationDivision
from organisations.tests.factories import (
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
)
from .base_tests import BaseElectionCreatorMixIn


class TestElectionBuilder(BaseElectionCreatorMixIn, TestCase):
    def test_eq(self):
        eb1 = ElectionBuilder("local", "2017-06-08")

        eb2 = (
            ElectionBuilder("local", "2017-06-08")
            .with_source("foo/bar.baz")
            .with_snooped_election(7)
        )

        # these should be 'equal' because only the meta-data differs
        self.assertEqual(eb1, eb2)

        eb2 = eb2.with_organisation(self.org1)

        # now these objects will build funamentally different elections
        self.assertNotEqual(eb1, eb2)

    def test_with_metadata(self):
        snooper = SnoopedElection.objects.create()
        builder = (
            ElectionBuilder("local", "2017-06-08")
            .with_organisation(self.org1)
            .with_division(self.org_div_1)
            .with_source("foo/bar.baz")
            .with_snooped_election(snooper.id)
        )
        election = builder.build_ballot(None)
        election.save()
        self.assertEqual("foo/bar.baz", election.source)
        assert isinstance(election.snooped_election, SnoopedElection)

    def test_invalid_subtype(self):
        naw_election_type = ElectionType.objects.get(election_type="naw")
        invalid_sub_type = ElectionSubType.objects.create(
            election_subtype="x", election_type=self.election_type1
        )
        builder = ElectionBuilder(naw_election_type, "2017-06-08")
        with self.assertRaises(ElectionSubType.ValidationError):
            builder.with_subtype(invalid_sub_type)

    def test_invalid_organisation(self):
        builder = ElectionBuilder("local", "2017-06-08")

        # delete the relationship between org1 and local elections
        self.elected_role1.delete()

        with self.assertRaises(Organisation.ValidationError):
            builder.with_organisation(self.org1)

    def test_organisation_date_range_invalid(self):
        builder = ElectionBuilder("local", "2001-01-01")

        # delete the relationship between org1 and local elections
        self.elected_role1.delete()

        with self.assertRaises(Organisation.ValidationError):
            builder.with_organisation(self.org1)

    def test_invalid_division_not_child_of_org(self):
        org2 = Organisation.objects.create(
            official_identifier="TEST2",
            organisation_type="local-authority",
            official_name="Test Council",
            slug="test2",
            territory_code="ENG",
            election_name="Test2 Council Local Elections",
            start_date=date(2016, 10, 1),
        )
        ElectedRole.objects.create(
            election_type=self.election_type1,
            organisation=org2,
            elected_title="Local Councillor",
            elected_role_name="Councillor for Test2 Council",
        )
        builder = ElectionBuilder("local", "2017-06-08").with_organisation(org2)

        # self.org_div_1 is not a child of org2
        # its a child of self.org1
        with self.assertRaises(OrganisationDivision.ValidationError):
            builder.with_division(self.org_div_1)

    def test_invalid_division_wrong_subtype(self):
        naw_election_type = ElectionType.objects.get(election_type="naw")
        region_sub_type = ElectionSubType.objects.get(
            election_subtype="r", election_type=naw_election_type
        )
        naw_org = Organisation.objects.create(
            official_identifier="naw",
            organisation_type="naw",
            official_name="naw",
            slug="naw",
            territory_code="WLS",
            election_name="National Assembly for Wales elections",
            start_date=date(2016, 10, 1),
        )
        ElectedRole.objects.create(
            election_type=naw_election_type,
            organisation=naw_org,
            elected_title="Assembly Member",
            elected_role_name="Assembly Member for Foo",
        )

        naw_div_set = OrganisationDivisionSetFactory(organisation=naw_org)
        constituency_div = OrganisationDivisionFactory(
            divisionset=naw_div_set,
            name="Test Div",
            slug="test-div",
            division_election_sub_type="c",
        )
        builder = (
            ElectionBuilder("naw", "2017-06-08")
            .with_organisation(naw_org)
            .with_subtype(region_sub_type)
        )

        # constituency_div is a constituency
        # but this builder object expects a region
        with self.assertRaises(OrganisationDivision.ValidationError):
            builder.with_division(constituency_div)

    def test_seats_contested_local_election(self):
        builder = (
            ElectionBuilder("local", "2017-06-08")
            .with_organisation(self.org1)
            .with_division(self.org_div_1)
        )
        election = builder.build_ballot(None)
        election.save()
        self.assertIsNone(election.seats_contested)
        self.assertEqual(3, election.seats_total)

    def test_seats_contested_local_by_election(self):
        builder = (
            ElectionBuilder("local", "2017-06-08")
            .with_organisation(self.org1)
            .with_division(self.org_div_1)
            .with_contest_type("by")
        )
        election = builder.build_ballot(None)
        election.save()
        self.assertEqual(1, election.seats_contested)
        self.assertEqual(3, election.seats_total)

    def test_with_groups(self):
        builder = (
            ElectionBuilder("local", "2017-06-08")
            .with_organisation(self.org1)
            .with_division(self.org_div_1)
        )
        election_group = builder.build_election_group()
        org_group = builder.build_organisation_group(election_group)
        ballot = builder.build_ballot(org_group)
        ballot.save()

        # calling save() on the ballot object
        # should also save its 2x parent groups
        self.assertEqual(3, Election.private_objects.all().count())
        self.assertIsNotNone(election_group.id)
        self.assertIsNotNone(org_group.id)
        self.assertIsNotNone(ballot.id)

    def test_created_with_status(self):
        builder = (
            ElectionBuilder("local", "2017-06-08")
            .with_organisation(self.org1)
            .with_division(self.org_div_1)
        )
        election_group = builder.build_election_group()
        org_group = builder.build_organisation_group(election_group)
        ballot = builder.build_ballot(org_group)
        ballot.save()

        default_status = DEFAULT_STATUS

        self.assertEqual(default_status, ballot.moderation_status.short_label)
        self.assertEqual(default_status, org_group.moderation_status.short_label)
        self.assertEqual(default_status, election_group.moderation_status.short_label)
