import json
from datetime import datetime, timedelta

import vcr
from rest_framework.test import APITestCase

from elections.tests.factories import ElectionFactory
from organisations.tests.factories import (
    OrganisationFactory, OrganisationDivisionFactory)
from elections.models import MetaData


class TestElectionAPIQueries(APITestCase):
    lat = 51.5010089365
    lon = -0.141587600123

    fixtures = ['onspd.json']

    def test_election_endpoint(self):
        id = ElectionFactory(group=None).election_id
        resp = self.client.get("/api/elections/")
        data = resp.json()

        assert len(data['results']) == 1
        assert data['results'][0]['election_id'] == id

    def test_election_endpoint_current(self):
        id_current = ElectionFactory(
            group=None, poll_open_date=datetime.today()).election_id
        id_future = ElectionFactory(  # noqa
            group=None,
            poll_open_date=datetime.today() - timedelta(days=60)).election_id

        resp = self.client.get("/api/elections/?current")
        data = resp.json()

        assert len(data['results']) == 1
        assert data['results'][0]['election_id'] == id_current
        assert data['results'][0]['current'] == True


    def test_election_endpoint_future(self):
        ElectionFactory(
            group=None,
            poll_open_date=datetime.today(),
            election_id="local.place-name-future-election.2017-03-23")
        ElectionFactory(
            group=None, poll_open_date=datetime.today() - timedelta(days=1))

        resp = self.client.get("/api/elections/?future")
        data = resp.json()

        assert len(data['results']) == 1
        assert data['results'][0]['election_id'] == \
            "local.place-name-future-election.2017-03-23"

    def test_election_endpoint_for_postcode(self):
        election_id = "local.place-name.2017-03-23"
        ElectionFactory(group=None, election_id=election_id)
        ElectionFactory(group=None, division_geography=None)
        resp = self.client.get("/api/elections/?postcode=SW1A1AA")
        data = resp.json()

        assert len(data['results']) == 1
        assert data['results'][0]['election_id'] == election_id

    def test_election_endpoint_for_postcode_jsonp(self):
        election_id = "local.place-name.2017-03-23"
        ElectionFactory(group=None, election_id=election_id)
        ElectionFactory(group=None, division_geography=None)
        url = "/api/elections/?postcode=SW1A1AA" + \
              "&format=jsonp&callback=a_callback_string"
        resp = self.client.get(url)
        assert resp.content.decode('utf8').startswith("a_callback_string(")

    def test_election_endpoint_for_postcode_cors(self):
        election_id = "local.place-name.2017-03-23"
        ElectionFactory(group=None, election_id=election_id)
        ElectionFactory(group=None, division_geography=None)
        url = "/api/elections/?postcode=SW1A1AA"
        resp = self.client.get(url, HTTP_ORIGIN='foo.bar/baz')
        self.assertEqual(resp.get('Access-Control-Allow-Origin'), '*')

    @vcr.use_cassette(
        'fixtures/vcr_cassettes/test_election_for_bad_postcode.yaml')
    def test_election_endpoint_for_bad_postcode(self):
        election_id = "local.place-name.2017-03-23"
        ElectionFactory(group=None, election_id=election_id)
        ElectionFactory(group=None, division_geography=None)
        resp = self.client.get("/api/elections/?postcode=SW1A1AX")
        data = resp.json()

        assert data['detail'] == "Invalid postcode"

    def test_election_endpoint_for_lat_lng(self):
        election_id = "local.place-name.2017-03-23"
        ElectionFactory(group=None, election_id=election_id)
        ElectionFactory(group=None, division_geography=None)

        resp = self.client.get(
            "/api/elections/?coords=51.5010089365,-0.141587600123")
        data = resp.json()

        assert data['results'][0]['election_id'] == election_id
        assert len(data['results']) == 1

    def test_metadata_filter(self):
        election = ElectionFactory(group=None, poll_open_date=datetime.today())
        resp = self.client.get(
            "/api/elections/?metadata=1")
        data = resp.json()
        assert data['count'] == 0
        metadata = MetaData.objects.create(
            description="just a test",
            data = """
            {
                "2018-05-03-id-pilot": {
                  "title": "You need to show ID to vote at this election",
                  "url": "https://www.woking.gov.uk/voterid",
                  "detail": "
                      Voters in Woking will be required to show photo
                      ID before they can vote.
                     "
                }
              }
            """,
        )

        election.metadata = metadata
        election.save()
        resp = self.client.get(
            "/api/elections/?metadata=1")
        data = resp.json()
        assert data['count'] == 1

    def test_all_expected_fields_returned(self):

        org = OrganisationFactory()
        org_div = OrganisationDivisionFactory(
            organisation=org, territory_code="ENG")
        ElectionFactory(group=None, organisation=org, division=org_div)

        self.expected_object = json.loads("""
        {
            "group_type": null,
            "current": false,
            "poll_open_date": "2017-03-23",
            "election_id": "local.place-name-0.2017-03-23",
            "group": null,
            "division": {
                "name": "Division 0",
                "slug": "0",
                "geography_curie": "0",
                "divisionset": {
                    "start_date": "2017-05-04",
                    "legislation_url": "https://example.com/the-law",
                    "short_title": "Made up boundary changes",
                    "notes": "This is just for testing.",
                    "end_date": "2025-05-03",
                    "consultation_url": "https://example.com/consultation",
                    "mapit_generation_id": ""
                },
                "mapit_generation_high": null,
                "seats_total": null,
                "division_election_sub_type": "",
                "division_subtype": "",
                "mapit_generation_low": null,
                "division_type": "test",
                "official_identifier": "0",
                "territory_code": "ENG"
            },
            "election_type": {
                "name": "Local elections",
                "election_type": "local"
            },
            "explanation": null,
            "voting_system": {
                "slug": "",
                "name": "",
                "uses_party_lists": false
            },
            "children": [],
            "election_subtype": null,
            "organisation": {
                "url": "http://testserver/api/organisations/local-authority/0/2016-10-01/",
                "slug": "org-0",
                "territory_code": "ENG",
                "organisation_subtype": "",
                "common_name": "Organisation 0",
                "official_name": "The Organisation 0 Council",
                "organisation_type": "local-authority",
                "election_name": "",
                "official_identifier": "0",
                "start_date": "2016-10-01",
                "end_date": null
            },
            "election_title": "Election 0",
            "elected_role": "Councillor",
            "seats_contested": 1,
            "tmp_election_id": null,
            "metadata": null
        }
        """)

        resp = self.client.get("/api/elections/")
        data = resp.json()
        self.assertEqual(data['results'][0], self.expected_object)

        resp = self.client.get("/api/elections/local.place-name-0.2017-03-23/")
        data = resp.json()
        self.assertEqual(data, self.expected_object)

        resp = self.client.get(
            "/api/elections/local.place-name-0.2017-03-23/geo/",
            content_type="application/json")
        data = resp.json()
        self.assertEqual(data['properties'], self.expected_object)
