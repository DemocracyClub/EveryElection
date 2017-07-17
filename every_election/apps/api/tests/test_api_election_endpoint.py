import json
from datetime import datetime, timedelta

import vcr
from rest_framework.test import APITestCase

from elections.tests.factories import ElectionFactory
from organisations.tests.factories import (
    OrganisationFactory, OrganisationDivisionFactory)


class TestElectionAPIQueries(APITestCase):
    lat = 51.5010089365
    lon = -0.141587600123

    def test_election_endpoint(self):
        id = ElectionFactory(group=None).election_id
        resp = self.client.get("/api/elections/")
        data = resp.json()

        assert len(data['results']) == 1
        assert data['results'][0]['election_id'] == id

    def test_election_endpoint_current(self):
        id_current = ElectionFactory(
            group=None, poll_open_date=datetime.today()).election_id
        id_future = ElectionFactory(
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

    @vcr.use_cassette(
        'fixtures/vcr_cassettes/test_election_for_postcode.yaml')
    def test_election_endpoint_for_postcode(self):
        election_id = "local.place-name.2017-03-23"
        ElectionFactory(group=None, election_id=election_id)
        ElectionFactory(group=None, geography=None)
        resp = self.client.get("/api/elections/?postcode=SW1A1AA")
        data = resp.json()

        assert len(data['results']) == 1
        assert data['results'][0]['election_id'] == election_id

    @vcr.use_cassette(
        'fixtures/vcr_cassettes/test_election_for_bad_postcode.yaml')
    def test_election_endpoint_for_bad_postcode(self):
        election_id = "local.place-name.2017-03-23"
        ElectionFactory(group=None, election_id=election_id)
        ElectionFactory(group=None, geography=None)
        resp = self.client.get("/api/elections/?postcode=SW1A1AX")
        data = resp.json()

        assert data['detail'] == "Invalid postcode"

    def test_election_endpoint_for_lat_lng(self):
        election_id = "local.place-name.2017-03-23"
        ElectionFactory(group=None, election_id=election_id)
        ElectionFactory(group=None, geography=None)

        resp = self.client.get(
            "/api/elections/?coords=51.5010089365,-0.141587600123")
        data = resp.json()

        assert data['results'][0]['election_id'] == election_id
        assert len(data['results']) == 1

    def test_all_expected_fields_returned(self):
        org = OrganisationFactory()
        org_div = OrganisationDivisionFactory(
            organisation=org, territory_code="ENG")
        ElectionFactory(group=None, organisation=org, division=org_div)

        resp = self.client.get("/api/elections/")

        print(json.dumps(resp.json(), indent=4))
        assert resp.json() == json.loads("""
        {
            "next": null,
            "previous": null,
            "results": [
                {
                    "group_type": null,
                    "current": false,
                    "poll_open_date": "2017-03-23",
                    "election_id": "local.place-name-0.2017-03-23",
                    "group": null,
                    "division": {
                        "name": "Division 0",
                        "slug": "0",
                        "geography_curie": "test:0",
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
                        "slug": "org-0",
                        "territory_code": "ENG",
                        "organisation_subtype": "",
                        "common_name": "Organisation 0",
                        "official_name": "The Organisation 0 Council",
                        "organisation_type": "local-authority",
                        "election_name": "",
                        "official_identifier": "0",
                        "gss": "E000000"
                    },
                    "election_title": "Election 0",
                    "elected_role": "Councillor",
                    "tmp_election_id": null
                }
            ],
            "count": 1
        }
        """)



