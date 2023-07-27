from datetime import date

from django.test import TestCase
from election_snooper.models import SnoopedElection
from elections.models import (
    DEFAULT_STATUS,
    ElectedRole,
    Election,
    ElectionSubType,
    ElectionType,
)
from elections.utils import ElectionBuilder
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

    def test_get_seats_contested(self):
        sp_election_type = ElectionType.objects.get(election_type="sp")
        region_sub_type = ElectionSubType.objects.get(
            election_subtype="r", election_type=sp_election_type
        )
        constituency_sub_type = ElectionSubType.objects.get(
            election_subtype="c", election_type=sp_election_type
        )
        sp_org = Organisation.objects.create(
            official_identifier="sp",
            organisation_type="sp",
            official_name="Scottish Parliament",
            slug="sp",
            election_name="Scottish parliament election",
            territory_code="SCT",
            start_date=date(1999, 5, 6),
        )

        ElectedRole.objects.create(
            election_type=sp_election_type,
            organisation=sp_org,
            elected_title="Member of the Scottish Parliament",
            elected_role_name="Member of the Scottish Parliament",
        )

        sp_div_set = OrganisationDivisionSetFactory(organisation=sp_org)

        sp_r_div = OrganisationDivisionFactory(
            divisionset=sp_div_set,
            name="sp Div 1",
            slug="sp-div-1",
            seats_total=7,
            division_election_sub_type="r",
        )
        sp_c_div = OrganisationDivisionFactory(
            divisionset=sp_div_set,
            name="sp Div 2",
            slug="sp-div-2",
            division_election_sub_type="c",
        )

        builder_1 = (
            ElectionBuilder("sp", "2021-5-06")
            .with_organisation(sp_org)
            .with_division(sp_r_div)
            .with_subtype(region_sub_type)
        )
        builder_2 = (
            ElectionBuilder("sp", "2021-5-06")
            .with_organisation(sp_org)
            .with_division(sp_c_div)
            .with_subtype(constituency_sub_type)
        )

        ballot_1 = builder_1.build_ballot(None)
        ballot_1.save()

        ballot_2 = builder_2.build_ballot(None)
        ballot_2.save()

        self.assertEqual(7, ballot_1.seats_contested)
        self.assertEqual(1, ballot_2.seats_contested)

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

        self.assertEqual(default_status, ballot.current_status)
        self.assertEqual(default_status, org_group.current_status)
        self.assertEqual(default_status, election_group.current_status)

    def test_can_create_duplicate_groups(self):
        """
        Regression test for https://github.com/DemocracyClub/EveryElection/issues/1162

        If an ID exists for the organisation after creating a ballot ID, later
        attempts to createt another balot ID for the org on the same day failed
        due to a duplicate key error.

        """
        # A user submits an election for an organisation and save it
        builder = (
            ElectionBuilder("local", "2017-06-08")
            .with_organisation(self.org1)
            .with_division(self.org_div_1)
        )
        election_group = builder.build_election_group().save()
        org_group = builder.build_organisation_group(election_group).save()
        ballot = builder.build_ballot(org_group)
        ballot.save()

        # Later, a user submits another election for that organisation, on the
        # same day, in a differnet division
        builder = (
            ElectionBuilder("local", "2017-06-08")
            .with_organisation(self.org1)
            .with_division(self.org_div_2)
        )
        election_group = builder.build_election_group().save()
        org_group = builder.build_organisation_group(election_group).save()
        ballot = builder.build_ballot(org_group)
        ballot.save()
