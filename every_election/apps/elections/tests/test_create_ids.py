from datetime import date

from django.test import TestCase
from elections.models import (
    ElectedRole,
    Election,
    ElectionSubType,
    ElectionType,
)
from organisations.models import Organisation
from organisations.tests.factories import (
    DivisionGeographyFactory,
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
    OrganisationGeographyFactory,
)

from ..utils import reset_cache
from .base_tests import BaseElectionCreatorMixIn, FuzzyInt


class TestCreateIds(BaseElectionCreatorMixIn, TestCase):
    def setUp(self):
        super().setUp()
        reset_cache()

    def run_test_with_data(
        self, all_data, expected_ids, expected_titles, **kwargs
    ):
        self.create_ids(all_data, **kwargs)
        assert Election.private_objects.count() == len(expected_ids)

        # ensure the records created match the expected ids
        for expected_id in expected_ids:
            assert Election.private_objects.filter(
                election_id=expected_id
            ).exists()

        # ensure the records created match the expected titles
        for expected_title in expected_titles:
            assert Election.private_objects.filter(
                election_title=expected_title
            ).exists()

        # ensure group relationships have been saved correctly
        for election in Election.private_objects.all():
            if election.group_type != "election":
                assert isinstance(election.group_id, int)

    def test_group_id(self):
        self.run_test_with_data(
            self.base_data, ["local." + self.date_str], ["Local elections"]
        )

    def test_creates_div_data_ids(self):
        self.assertEqual(Election.private_objects.count(), 0)
        all_data = self.base_data
        all_data["election_divisions"] = [
            self.add_division(self.make_div_id(), ballot_type="contested")
        ]
        expected_ids = [
            "local." + self.date_str,
            "local.test." + self.date_str,
            "local.test.test-div." + self.date_str,
        ]
        expected_titles = [
            "Local elections",
            "Test Council local elections",
            "Test Council local elections Test Div 1",
        ]

        self.run_test_with_data(all_data, expected_ids, expected_titles)

    def test_creates_div_data_ids_two_divs(self):
        all_data = self.base_data

        all_data["election_divisions"] = [
            self.add_division(self.make_div_id(), ballot_type="contested"),
            self.add_division(
                self.make_div_id(div=self.org_div_2), ballot_type="contested"
            ),
        ]

        expected_ids = [
            "local." + self.date_str,
            "local.test." + self.date_str,
            "local.test.test-div." + self.date_str,
            "local.test.test-div-2." + self.date_str,
        ]
        expected_titles = [
            "Local elections",
            "Test Council local elections",
            "Test Council local elections Test Div 1",
            "Test Council local elections Test Div 2",
        ]

        self.run_test_with_data(all_data, expected_ids, expected_titles)

    def test_creates_ids_two_orgs(self):
        org2 = Organisation.objects.create(
            official_identifier="TEST2",
            organisation_type="local-authority",
            official_name="Test Council 2",
            slug="test2",
            territory_code="ENG",
            election_name="Test Council 2 local elections",
            start_date=date(2016, 10, 1),
        )
        ElectedRole.objects.create(
            election_type=self.election_type1,
            organisation=org2,
            elected_title="Local Councillor",
            elected_role_name="Councillor for Test Council 2",
        )
        div_set2 = OrganisationDivisionSetFactory(organisation=org2)
        div3 = OrganisationDivisionFactory(
            divisionset=div_set2, name="Test Div 3", slug="test-div-3"
        )

        all_data = self.base_data
        all_data["election_organisation"] = [self.org1, org2]
        all_data["election_divisions"] = [
            self.add_division(
                self.make_div_id(),
                ballot_type="contested",
            ),
            self.add_division(
                self.make_div_id(org=org2, div=div3),
                ballot_type="contested",
            ),
        ]

        expected_ids = [
            "local." + self.date_str,
            "local.test." + self.date_str,
            "local.test2." + self.date_str,
            "local.test.test-div." + self.date_str,
            "local.test2.test-div-3." + self.date_str,
        ]
        expected_titles = [
            "Local elections",
            "Test Council local elections",
            "Test Council 2 local elections",
            "Test Council local elections Test Div 1",
            "Test Council 2 local elections Test Div 3",
        ]

        self.run_test_with_data(all_data, expected_ids, expected_titles)

    def test_creates_div_data_ids_blank_divs(self):
        all_data = self.base_data

        all_data["election_divisions"] = [
            self.add_division(self.make_div_id()),
            self.add_division(
                self.make_div_id(div=self.org_div_2), ballot_type=""
            ),
        ]

        expected_ids = [
            "local." + self.date_str,
            "local.test." + self.date_str,
            "local.test.test-div." + self.date_str,
        ]
        expected_titles = [
            "Local elections",
            "Test Council local elections",
            "Test Council local elections Test Div 1",
        ]

        self.run_test_with_data(all_data, expected_ids, expected_titles)

    def test_creates_by_election(self):
        all_data = self.base_data

        all_data["election_divisions"] = [
            self.add_division(self.make_div_id(), ballot_type="by_election"),
            self.add_division(
                self.make_div_id(div=self.org_div_2), ballot_type="by_election"
            ),
        ]

        expected_ids = [
            "local." + self.date_str,
            "local.test." + self.date_str,
            "local.test.test-div.by." + self.date_str,
            "local.test.test-div-2.by." + self.date_str,
        ]
        expected_titles = [
            "Local elections",
            "Test Council local elections",
            "Test Council local elections Test Div 1 by-election",
            "Test Council local elections Test Div 2 by-election",
        ]

        self.run_test_with_data(all_data, expected_ids, expected_titles)

        for election in Election.private_objects.filter(group_type=None):
            assert "by-election" in election.election_title

    def test_creates_mayor_id(self):
        mayor_org = Organisation.objects.create(
            official_identifier="MAYORTEST1",
            organisation_type="combined-authority",
            official_name="Test authority",
            slug="test-ca",
            territory_code="ENG",
            election_name="Test Council Mayoral elections",
            start_date=date(2016, 10, 1),
        )
        mayor_election_type = ElectionType.objects.get(election_type="mayor")
        ElectedRole.objects.create(
            election_type=mayor_election_type,
            organisation=mayor_org,
            elected_title="Mayor",
            elected_role_name="Mayor of Foo Town",
        )

        all_data = {
            "election_organisation": [mayor_org],
            "election_type": mayor_election_type,
            "date": self.date,
        }

        expected_ids = [
            "mayor." + self.date_str,
            "mayor.test-ca." + self.date_str,
        ]
        expected_titles = ["Mayoral elections", "Mayor of Foo Town"]

        self.run_test_with_data(all_data, expected_ids, expected_titles)

        ballot = Election.private_objects.get(
            election_id="mayor.test-ca." + self.date_str
        )
        self.assertIsNone(ballot.group_type)

    def test_creates_parl_id(self):
        parl_org = Organisation.objects.create(
            official_identifier="parl",
            organisation_type="parl",
            official_name="Parl",
            slug="parl",
            territory_code="ENG",
            election_name="General Election",
            start_date=date(2016, 10, 1),
        )
        parl_election_type = ElectionType.objects.get(election_type="parl")
        ElectedRole.objects.create(
            election_type=parl_election_type,
            organisation=parl_org,
            elected_title="Member of Parliament",
            elected_role_name="Member of Parliament",
        )

        all_data = {
            "election_organisation": [parl_org],
            "election_type": parl_election_type,
            "date": self.date,
        }

        expected_ids = ["parl." + self.date_str]
        expected_titles = ["UK Parliament elections"]

        self.run_test_with_data(all_data, expected_ids, expected_titles)

    def test_creates_naw_id(self):
        naw_org = Organisation.objects.create(
            official_identifier="naw",
            organisation_type="naw",
            official_name="naw",
            slug="naw",
            territory_code="WLS",
            election_name="National Assembly for Wales elections",
            start_date=date(2016, 10, 1),
        )
        naw_election_type = ElectionType.objects.get(election_type="naw")
        naw_election_sub_type_c = ElectionSubType.objects.get(
            election_subtype="c", election_type=naw_election_type
        )
        naw_election_sub_type_r = ElectionSubType.objects.get(
            election_subtype="r", election_type=naw_election_type
        )
        ElectedRole.objects.create(
            election_type=naw_election_type,
            organisation=naw_org,
            elected_title="Assembly Member",
            elected_role_name="Assembly Member for Foo",
        )
        naw_div_set = OrganisationDivisionSetFactory(organisation=naw_org)
        org_div_3 = OrganisationDivisionFactory(
            divisionset=naw_div_set,
            name="Test Div 3",
            slug="test-div-3",
            division_election_sub_type="c",
        )
        org_div_4 = OrganisationDivisionFactory(
            divisionset=naw_div_set,
            name="Test Div 4",
            slug="test-div-4",
            division_election_sub_type="c",
        )
        org_div_5 = OrganisationDivisionFactory(
            divisionset=naw_div_set,
            name="Test Div 5",
            slug="test-div-5",
            division_election_sub_type="r",
        )

        all_data = {
            "election_organisation": [naw_org],
            "election_type": naw_election_type,
            "election_subtype": [
                naw_election_sub_type_c,
                naw_election_sub_type_r,
            ],
            "date": self.date,
        }

        all_data["election_divisions"] = [
            # contested seat
            self.add_division(
                self.make_div_id(org=naw_org, div=org_div_3, subtype="c"),
                ballot_type="contested",
            ),
            # by election
            self.add_division(
                self.make_div_id(org=naw_org, div=org_div_4, subtype="c"),
                ballot_type="by_election",
            ),
            # contested seat
            self.add_division(
                self.make_div_id(org=naw_org, div=org_div_5, subtype="r"),
                ballot_type="contested",
            ),
        ]

        expected_ids = [
            "naw." + self.date_str,
            "naw.c." + self.date_str,
            "naw.r." + self.date_str,
            "naw.c.test-div-3." + self.date_str,  # no 'by' suffix
            "naw.c.test-div-4.by." + self.date_str,  # 'by' suffix
            "naw.r.test-div-5." + self.date_str,
        ]
        expected_titles = [
            "National Assembly for Wales elections",
            "National Assembly for Wales elections (Constituencies)",
            "National Assembly for Wales elections (Regions)",
            "National Assembly for Wales elections (Constituencies) Test Div 3",
            "National Assembly for Wales elections (Constituencies) Test Div 4 by-election",
            "National Assembly for Wales elections (Regions) Test Div 5",
        ]

        self.run_test_with_data(
            all_data,
            expected_ids,
            expected_titles,
            subtypes=[naw_election_sub_type_c, naw_election_sub_type_r],
        )

    def test_election_with_organisation_geography(self):
        all_data = self.base_data

        OrganisationGeographyFactory(
            organisation=all_data["election_organisation"][0],
            geography=self.test_polygon,
        )

        all_data["election_divisions"] = [
            self.add_division(
                self.make_div_id(),
                ballot_type="contested",
            ),
            self.add_division(
                self.make_div_id(div=self.org_div_2),
                ballot_type="contested",
            ),
        ]

        expected_ids = [
            "local." + self.date_str,
            "local.test." + self.date_str,
            "local.test.test-div." + self.date_str,
            "local.test.test-div-2." + self.date_str,
        ]
        expected_titles = [
            "Local elections",
            "Test Council local elections",
            "Test Council local elections Test Div 1",
            "Test Council local elections Test Div 2",
        ]

        self.run_test_with_data(all_data, expected_ids, expected_titles)

        for election in Election.private_objects.all():
            if election.group_type == "organisation":
                self.assertTrue(election.geography is not None)
            else:
                self.assertTrue(election.geography is None)

        result = Election.private_objects.for_lat_lng(
            51.50124158773981, -0.13715744018554688
        )
        self.assertEqual(1, len(result))
        self.assertEqual("local.test." + self.date_str, result[0].election_id)

    def test_election_with_division_geography(self):
        all_data = self.base_data

        DivisionGeographyFactory(
            division=self.org_div_2, geography=self.test_polygon
        )

        all_data["election_divisions"] = [
            self.add_division(
                self.make_div_id(),
                ballot_type="contested",
            ),
            self.add_division(
                self.make_div_id(div=self.org_div_2),
                ballot_type="contested",
            ),
        ]

        expected_ids = [
            "local." + self.date_str,
            "local.test." + self.date_str,
            "local.test.test-div." + self.date_str,
            "local.test.test-div-2." + self.date_str,
        ]
        expected_titles = [
            "Local elections",
            "Test Council local elections",
            "Test Council local elections Test Div 1",
            "Test Council local elections Test Div 2",
        ]

        self.run_test_with_data(all_data, expected_ids, expected_titles)

        for election in Election.private_objects.all():
            if election.election_id == "local.test.test-div-2." + self.date_str:
                self.assertTrue(election.geography is not None)
            else:
                self.assertTrue(election.geography is None)

        result = Election.private_objects.for_lat_lng(
            51.50124158773981, -0.13715744018554688
        )
        self.assertEqual(1, len(result))
        self.assertEqual(
            "local.test.test-div-2." + self.date_str, result[0].election_id
        )

    def test_gla_a_is_ballot(self):
        election_type = ElectionType.objects.get(election_type="gla")
        gla = Organisation.objects.create(
            official_identifier="gla",
            organisation_type="gla",
            official_name="Greater London Authority",
            slug="gla",
            territory_code="ENG",
            election_name="London Assembly election",
            start_date=date(2016, 10, 1),
        )
        gla.election_types.add(election_type)

        all_data = {
            "election_organisation": [gla],
            "election_subtype": [
                election_type.subtype.get(election_subtype="a")
            ],
            "election_type": election_type,
            "date": self.date,
            gla.pk: None,
            "{}_no_divs".format(gla.pk): "",
        }

        expected_ids = [
            "gla." + self.date_str,
            "gla.a." + self.date_str,
        ]
        expected_titles = [
            "Greater London Assembly elections",
            "Greater London Assembly elections (Additional)",
        ]
        with self.assertNumQueries(FuzzyInt(23, 27)):
            self.run_test_with_data(
                all_data,
                expected_ids,
                expected_titles,
                subtypes=all_data["election_subtype"],
            )

        ballot = Election.private_objects.get(election_id__startswith="gla.a.")
        self.assertIsNone(ballot.group_type)
