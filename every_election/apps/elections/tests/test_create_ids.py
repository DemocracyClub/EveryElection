from django.test import TestCase

from elections.models import (
    ElectedRole, Election, ElectionType, ElectionSubType)
from organisations.models import Organisation, DivisionGeography
from organisations.tests.factories import OrganisationDivisionFactory

from .base_tests import BaseElectionCreatorMixIn


class TestCreateIds(BaseElectionCreatorMixIn, TestCase):

    def run_test_with_data(self, all_data, expected_ids, **kwargs):
        self.create_ids(all_data, **kwargs)
        assert Election.objects.count() == len(expected_ids)

        # ensure the records created match the expected ids
        for expected_id in expected_ids:
            assert Election.objects.filter(election_id=expected_id).exists()

        # ensure group relationships have been saved correctly
        for election in Election.objects.all():
            if election.group_type != 'election':
                assert isinstance(election.group_id, int)

    def test_group_id(self):
        self.run_test_with_data(
            self.base_data,
            ['local.'+self.date_str, ]
        )

    def test_creates_div_data_ids(self):
        self.assertEqual(Election.objects.count(), 0)
        all_data = self.base_data
        all_data.update({self.make_div_id(): 'contested'})
        expected_ids = [
            'local.'+self.date_str,
            'local.test.'+self.date_str,
            'local.test.test-div.'+self.date_str,
        ]

        self.run_test_with_data(
            all_data,
            expected_ids
        )

    def test_creates_div_data_ids_two_divs(self):
        all_data = self.base_data

        all_data.update({
            self.make_div_id(): 'contested',
            self.make_div_id(div=self.org_div_2): 'contested',
        })
        expected_ids = [
            'local.'+self.date_str,
            'local.test.'+self.date_str,
            'local.test.test-div.'+self.date_str,
            'local.test.test-div-2.'+self.date_str,
        ]

        self.run_test_with_data(
            all_data,
            expected_ids
        )

    def test_creates_div_data_ids_blank_divs(self):
        all_data = self.base_data

        all_data.update({
            self.make_div_id(): 'contested',
            self.make_div_id(div=self.org_div_2): '',
        })
        expected_ids = [
            'local.'+self.date_str,
            'local.test.'+self.date_str,
            'local.test.test-div.'+self.date_str,
        ]

        self.run_test_with_data(
            all_data,
            expected_ids
        )

    def test_creates_by_election(self):
        all_data = self.base_data

        all_data.update({
            self.make_div_id(): 'by_election',
            self.make_div_id(div=self.org_div_2): 'by_election',
        })
        expected_ids = [
            'local.'+self.date_str,
            'local.test.'+self.date_str,
            'local.test.test-div.by.'+self.date_str,
            'local.test.test-div-2.by.'+self.date_str,
        ]

        self.run_test_with_data(
            all_data,
            expected_ids
        )

        for election in Election.objects.filter(group_type=None):
            assert 'by-election' in election.election_title

    def test_creates_mayor_id(self):
        mayor_org = Organisation.objects.create(
            official_identifier='MAYORTEST1',
            organisation_type='combined-authority',
            official_name="Test authority",
            gss="X10000001",
            slug="test-ca",
            territory_code="ENG",
            election_name="Test Council Mayoral Elections",
        )
        mayor_election_type = ElectionType.objects.get(
            election_type='mayor',
        )
        ElectedRole.objects.create(
            election_type=mayor_election_type,
            organisation=mayor_org,
            elected_title="Mayor",
            elected_role_name="Mayor of Foo Town",
        )


        all_data =  {
            'election_organisation': [mayor_org, ],
            'election_type': mayor_election_type,
            'date': self.date,
        }

        expected_ids = [
            'mayor.'+self.date_str,
            'mayor.test-ca.'+self.date_str,
        ]

        self.run_test_with_data(
            all_data,
            expected_ids
        )

    def test_creates_parl_id(self):
        parl_org = Organisation.objects.create(
            official_identifier='parl',
            organisation_type='parl',
            official_name="Parl",
            gss="X20000001",
            slug="parl",
            territory_code="ENG",
            election_name="General Election",
        )
        parl_election_type = ElectionType.objects.get(
            election_type='parl',
        )


        all_data =  {
            'election_organisation': [parl_org, ],
            'election_type': parl_election_type,
            'date': self.date,
        }

        expected_ids = [
            'parl.'+self.date_str,
        ]

        self.run_test_with_data(
            all_data,
            expected_ids
        )

    def test_creates_naw_id(self):
        naw_org = Organisation.objects.create(
            official_identifier='naw',
            organisation_type='naw',
            official_name="naw",
            gss="W20000001",
            slug="naw",
            territory_code="WLS",
            election_name="Welsh Assembly",
        )
        naw_election_type = ElectionType.objects.get(
            election_type='naw',
        )
        naw_election_sub_type = ElectionSubType.objects.get(
            election_subtype='c',
            election_type=naw_election_type,
        )
        ElectedRole.objects.create(
            election_type=naw_election_type,
            organisation=naw_org,
            elected_title="Assembly Member",
            elected_role_name="Assembly Member for Foo",
        )
        org_div_3 = OrganisationDivisionFactory(
            organisation=naw_org,
            name="Test Div 3",
            slug="test-div-3"
        )
        org_div_4 = OrganisationDivisionFactory(
            organisation=naw_org,
            name="Test Div 4",
            slug="test-div-4"
        )


        all_data =  {
            'election_organisation': [naw_org, ],
            'election_type': naw_election_type,
            'election_subtype': [naw_election_sub_type, ],
            'date': self.date,
        }

        all_data.update({
            self.make_div_id(
                org=naw_org, div=org_div_3): 'contested',  # contested seat
            self.make_div_id(
                org=naw_org, div=org_div_4): 'by_election',  # by election
        })

        expected_ids = [
            'naw.'+self.date_str,
            'naw.c.'+self.date_str,
            'naw.c.test-div-3.'+self.date_str,  # no 'by' suffix
            'naw.c.test-div-4.by.'+self.date_str,  # 'by' suffix
        ]

        self.run_test_with_data(
            all_data,
            expected_ids,
            subtypes=[naw_election_sub_type, ]
        )

    def test_election_with_organisation_geography(self):
        all_data = self.base_data

        geog = DivisionGeography()
        geog.organisation = all_data['election_organisation'][0]
        geog.geography = self.test_polygon
        geog.save()

        all_data.update({
            self.make_div_id(): 'contested',
            self.make_div_id(div=self.org_div_2): 'contested',
        })
        expected_ids = [
            'local.'+self.date_str,
            'local.test.'+self.date_str,
            'local.test.test-div.'+self.date_str,
            'local.test.test-div-2.'+self.date_str,
        ]

        self.run_test_with_data(
            all_data,
            expected_ids
        )

        for election in Election.objects.all():
            if election.group_type == 'organisation':
                self.assertTrue(election.geography != None)
            else:
                self.assertTrue(election.geography == None)

        result = Election.objects.for_lat_lng(
            51.50124158773981, -0.13715744018554688)
        self.assertEqual(1, len(result))
        self.assertEqual('local.test.'+self.date_str, result[0].election_id)


    def test_election_with_division_geography(self):
        all_data = self.base_data

        geog = DivisionGeography()
        geog.division = self.org_div_2
        geog.geography = self.test_polygon
        geog.save()

        all_data.update({
            self.make_div_id(): 'contested',
            self.make_div_id(div=self.org_div_2): 'contested',
        })
        expected_ids = [
            'local.'+self.date_str,
            'local.test.'+self.date_str,
            'local.test.test-div.'+self.date_str,
            'local.test.test-div-2.'+self.date_str,
        ]

        self.run_test_with_data(
            all_data,
            expected_ids
        )

        for election in Election.objects.all():
            if election.election_id == 'local.test.test-div-2.'+self.date_str:
                self.assertTrue(election.geography != None)
            else:
                self.assertTrue(election.geography == None)

        result = Election.objects.for_lat_lng(
            51.50124158773981, -0.13715744018554688)
        self.assertEqual(1, len(result))
        self.assertEqual('local.test.test-div-2.'+self.date_str, result[0].election_id)
