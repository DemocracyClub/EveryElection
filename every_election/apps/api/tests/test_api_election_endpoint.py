import json
from datetime import datetime, timedelta
from urllib.parse import urlencode

import vcr
from rest_framework.test import APITestCase

from elections.tests.factories import (
    ElectionWithStatusFactory,
    ModerationHistoryFactory,
    ModerationStatusFactory,
    related_status,
)
from organisations.tests.factories import (
    OrganisationFactory,
    OrganisationDivisionSetFactory,
    OrganisationDivisionFactory,
)
from elections.models import ElectionType, MetaData


class TestElectionAPIQueries(APITestCase):
    lat = 51.5010089365
    lon = -0.141587600123

    fixtures = ["onspd.json"]

    def test_election_endpoint(self):
        id_ = ElectionWithStatusFactory(group=None).election_id
        resp = self.client.get("/api/elections/")
        data = resp.json()

        assert len(data["results"]) == 1
        assert data["results"][0]["election_id"] == id_

    def test_election_endpoint_current(self):
        id_current = ElectionWithStatusFactory(
            group=None, poll_open_date=datetime.today()
        ).election_id
        id_future = ElectionWithStatusFactory(  # noqa
            group=None, poll_open_date=datetime.today() - timedelta(days=60)
        ).election_id

        resp = self.client.get("/api/elections/?current")
        data = resp.json()

        assert len(data["results"]) == 1
        assert data["results"][0]["election_id"] == id_current
        assert data["results"][0]["current"] == True

    def test_election_endpoint_future(self):
        ElectionWithStatusFactory(
            group=None,
            poll_open_date=datetime.today(),
            election_id="local.place-name-future-election.2017-03-23",
        )
        ElectionWithStatusFactory(
            group=None, poll_open_date=datetime.today() - timedelta(days=1)
        )

        resp = self.client.get("/api/elections/?future")
        data = resp.json()

        assert len(data["results"]) == 1
        assert (
            data["results"][0]["election_id"]
            == "local.place-name-future-election.2017-03-23"
        )

    def test_election_endpoint_for_postcode(self):
        election_id = "local.place-name.2017-03-23"
        ElectionWithStatusFactory(group=None, election_id=election_id)
        ElectionWithStatusFactory(group=None, division_geography=None)

        # we should monitor this and be aware if this number increases
        with self.assertNumQueries(9):
            resp = self.client.get("/api/elections/?postcode=SW1A1AA")

        data = resp.json()

        assert len(data["results"]) == 1
        assert data["results"][0]["election_id"] == election_id

    def test_election_endpoint_for_postcode_jsonp(self):
        election_id = "local.place-name.2017-03-23"
        ElectionWithStatusFactory(group=None, election_id=election_id)
        ElectionWithStatusFactory(group=None, division_geography=None)
        url = (
            "/api/elections/?postcode=SW1A1AA"
            + "&format=jsonp&callback=a_callback_string"
        )
        resp = self.client.get(url)
        assert resp.content.decode("utf8").startswith("a_callback_string(")

    def test_election_endpoint_for_postcode_cors(self):
        election_id = "local.place-name.2017-03-23"
        ElectionWithStatusFactory(group=None, election_id=election_id)
        ElectionWithStatusFactory(group=None, division_geography=None)
        url = "/api/elections/?postcode=SW1A1AA"
        resp = self.client.get(url, HTTP_ORIGIN="foo.bar/baz")
        self.assertEqual(resp.get("Access-Control-Allow-Origin"), "*")

    def test_election_endpoint_for_invalid_postcode(self):
        election_id = "local.place-name.2017-03-23"
        ElectionWithStatusFactory(group=None, election_id=election_id)
        ElectionWithStatusFactory(group=None, division_geography=None)
        # this input should fail the validation check
        resp = self.client.get("/api/elections/?postcode=not-a-postcode")
        data = resp.json()
        assert data["detail"] == "Invalid postcode"

    @vcr.use_cassette("fixtures/vcr_cassettes/test_election_for_bad_postcode.yaml")
    def test_election_endpoint_for_bad_postcode(self):
        election_id = "local.place-name.2017-03-23"
        ElectionWithStatusFactory(group=None, election_id=election_id)
        ElectionWithStatusFactory(group=None, division_geography=None)
        # this input passes the validation check
        # but when we call out to mapit we can't find it
        resp = self.client.get("/api/elections/?postcode=SW1A1AX")
        data = resp.json()

        assert data["detail"] == "Invalid postcode"

    def test_election_endpoint_for_lat_lng(self):
        election_id = "local.place-name.2017-03-23"
        ElectionWithStatusFactory(group=None, election_id=election_id)
        ElectionWithStatusFactory(group=None, division_geography=None)

        resp = self.client.get("/api/elections/?coords=51.5010089365,-0.141587600123")
        data = resp.json()

        assert data["results"][0]["election_id"] == election_id
        assert len(data["results"]) == 1

    def test_metadata_filter(self):
        election = ElectionWithStatusFactory(
            group=None, poll_open_date=datetime.today()
        )
        resp = self.client.get("/api/elections/?metadata=1")
        data = resp.json()
        assert data["count"] == 0
        metadata = MetaData.objects.create(
            description="just a test",
            data="""
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
        resp = self.client.get("/api/elections/?metadata=1")
        data = resp.json()
        assert data["count"] == 1

    def test_deleted_filter_list(self):
        approved = ElectionWithStatusFactory(
            group=None, moderation_status=related_status("Approved")
        )
        deleted = ElectionWithStatusFactory(
            group=None, moderation_status=related_status("Deleted")
        )
        ElectionWithStatusFactory(
            group=None, moderation_status=related_status("Rejected")
        )
        ElectionWithStatusFactory(
            group=None, moderation_status=related_status("Suggested")
        )

        resp = self.client.get("/api/elections/")
        data = resp.json()
        self.assertEqual(1, data["count"])
        self.assertEqual(data["results"][0]["election_id"], approved.election_id)
        self.assertEqual(data["results"][0]["deleted"], False)

        resp = self.client.get("/api/elections/?deleted=1")
        data = resp.json()
        self.assertEqual(1, data["count"])
        self.assertEqual(data["results"][0]["election_id"], deleted.election_id)
        self.assertEqual(data["results"][0]["deleted"], True)

    def test_deleted_filter_detail(self):
        election = ElectionWithStatusFactory(
            group=None, moderation_status=related_status("Deleted")
        )
        id_ = election.election_id

        resp = self.client.get("/api/elections/{}/".format(id_))
        self.assertEqual(404, resp.status_code)

        resp = self.client.get("/api/elections/{}/?deleted=1".format(id_))
        self.assertEqual(200, resp.status_code)

    def test_detail_invalid_id(self):
        resp = self.client.get("/api/elections/foo/")
        self.assertEqual(400, resp.status_code)

    def test_identifier_type_filter(self):
        group = ElectionWithStatusFactory(
            group_type="election", moderation_status=related_status("Approved")
        )
        ballot = ElectionWithStatusFactory(
            group=group, moderation_status=related_status("Approved")
        )

        resp = self.client.get("/api/elections/?identifier_type=election")
        data = resp.json()
        self.assertEqual(1, data["count"])
        self.assertEqual(data["results"][0]["election_id"], group.election_id)

        resp = self.client.get("/api/elections/?identifier_type=ballot")
        data = resp.json()
        self.assertEqual(1, data["count"])
        self.assertEqual(data["results"][0]["election_id"], ballot.election_id)

        resp = self.client.get("/api/elections/?identifier_type=organisation")
        data = resp.json()
        self.assertEqual(0, data["count"])

        resp = self.client.get("/api/elections/?identifier_type=foobar")
        data = resp.json()
        self.assertEqual(0, data["count"])

    def test_election_id_regex_filters(self):
        """
        Test using a simple regex to:
        - exclude all elections by election type
        - filter all elections by election type
        """
        # create an Election for every ElectionType
        election_types = list(
            ElectionType.objects.values_list("election_type", flat=True).distinct()
        )
        total_election_types = len(election_types)
        for election_type in election_types:
            election = ElectionWithStatusFactory(
                group_type="election",
                election_id=f"{election_type}.foo.2021-10-07",
                moderation_status=related_status("Approved"),
                election_type__election_type=election_type,
            )
            setattr(self, election_type, election)

        # test excluding each election type individually
        for election_type in election_types:
            with self.subTest(msg=election_type):
                regex = f"^{election_type}\..*"
                params = urlencode({"exclude_election_id_regex": regex})
                resp = self.client.get(f"/api/elections/?{params}")
                data = resp.json()
                election_types_returned = [
                    result["election_type"]["election_type"]
                    for result in data["results"]
                ]
                self.assertEqual(data["count"], total_election_types - 1)
                self.assertNotIn(election_type, election_types_returned)

        # test filtering each election type individually
        for election_type in election_types:
            with self.subTest(msg=election_type):
                regex = f"^{election_type}\..*"
                params = urlencode({"election_id_regex": regex})
                resp = self.client.get(f"/api/elections/?{params}")
                data = resp.json()
                election_types_returned = [
                    result["election_type"]["election_type"]
                    for result in data["results"]
                ]
                self.assertEqual(data["count"], 1)
                self.assertIn(election_type, election_types_returned)

    def test_organisation_filters(self):
        adu_election = ElectionWithStatusFactory(
            group_type="election",
            moderation_status=related_status("Approved"),
            organisation__official_identifier="ADU",
            organisation__start_date="1974-04-01",
            organisation__end_date="2021-07-20",
        )
        adu_election_new_start = ElectionWithStatusFactory(
            group_type="election",
            moderation_status=related_status("Approved"),
            organisation__official_identifier="ADU",
            organisation__start_date="2021-07-20",
        )
        wye_election = ElectionWithStatusFactory(
            group_type="election",
            moderation_status=related_status("Approved"),
            organisation__official_identifier="WYE",
        )
        parl_election = ElectionWithStatusFactory(
            group_type="election",
            moderation_status=related_status("Approved"),
            organisation__organisation_type="parl",
        )

        resp = self.client.get("/api/elections/?organisation_identifier=ADU")
        data = resp.json()
        self.assertEqual(2, data["count"])
        election_ids = [obj["election_id"] for obj in data["results"]]
        self.assertIn(adu_election.election_id, election_ids)
        self.assertIn(adu_election_new_start.election_id, election_ids)

        resp = self.client.get(
            "/api/elections/?organisation_identifier=ADU&organisation_start_date=1974-04-01"
        )
        data = resp.json()
        self.assertEqual(1, data["count"])
        self.assertEqual(data["results"][0]["election_id"], adu_election.election_id)

        resp = self.client.get("/api/elections/?organisation_identifier=WYE")
        data = resp.json()
        self.assertEqual(1, data["count"])
        self.assertEqual(data["results"][0]["election_id"], wye_election.election_id)

        resp = self.client.get("/api/elections/?organisation_identifier=foo")
        data = resp.json()
        self.assertEqual(0, data["count"])

        resp = self.client.get("/api/elections/?organisation_type=parl")
        data = resp.json()
        self.assertEqual(1, data["count"])
        self.assertEqual(data["results"][0]["election_id"], parl_election.election_id)

        resp = self.client.get("/api/elections/?organisation_type=foo")
        data = resp.json()
        self.assertEqual(0, data["count"])

    def test_child_visibility(self):
        # 4 ballots in the same group with different moderation statuses
        group = ElectionWithStatusFactory(
            group_type="election", moderation_status=related_status("Approved")
        )
        approved = ElectionWithStatusFactory(
            group=group, moderation_status=related_status("Approved")
        )
        suggested = ElectionWithStatusFactory(
            group=group, moderation_status=related_status("Suggested")
        )
        rejected = ElectionWithStatusFactory(
            group=group, moderation_status=related_status("Rejected")
        )
        deleted = ElectionWithStatusFactory(
            group=group, moderation_status=related_status("Deleted")
        )

        resp = self.client.get("/api/elections/{}/".format(group.election_id))
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        # only the approved child election should be in the response
        self.assertEqual(1, len(data["children"]))
        self.assertEqual([approved.election_id], data["children"])

        # delete the group
        ModerationHistoryFactory(
            election=group, status=ModerationStatusFactory(short_label="Deleted")
        )
        resp = self.client.get("/api/elections/{}/?deleted=1".format(group.election_id))
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        # deleted and approved child elections should be in the response
        self.assertTrue(deleted.election_id in data["children"])
        self.assertTrue(approved.election_id in data["children"])
        # we should never show suggested or rejected elections in API outputs
        self.assertTrue(suggested.election_id not in data["children"])
        self.assertTrue(rejected.election_id not in data["children"])

    def test_cancelled_election_with_replacement(self):
        cancelled = ElectionWithStatusFactory(group=None, cancelled=True)
        rescheduled = ElectionWithStatusFactory(group=None, replaces=cancelled)

        resp = self.client.get("/api/elections/{}/".format(cancelled.election_id))
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertTrue(data["cancelled"])
        self.assertEqual(rescheduled.election_id, data["replaced_by"])

        resp = self.client.get("/api/elections/{}/".format(rescheduled.election_id))
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertFalse(data["cancelled"])
        self.assertEqual(cancelled.election_id, data["replaces"])

    def test_all_expected_fields_returned(self):

        OrganisationFactory.reset_sequence(0)
        OrganisationDivisionFactory.reset_sequence(0)
        org = OrganisationFactory()
        div_set = OrganisationDivisionSetFactory(organisation=org)
        org_div = OrganisationDivisionFactory(divisionset=div_set, territory_code="ENG")
        ElectionWithStatusFactory(
            group=None, organisation=org, division=org_div, tags={"FOO": {"bar": "baz"}}
        )

        self.expected_object = json.loads(
            """
        {
            "group_type": null,
            "identifier_type": "ballot",
            "current": false,
            "poll_open_date": "2017-03-23",
            "election_id": "local.place-name-0.2017-03-23",
            "group": null,
            "division": {
                "name": "Division 0",
                "slug": "0",
                "divisionset": {
                    "start_date": "2017-05-04",
                    "legislation_url": "https://example.com/the-law",
                    "short_title": "Made up boundary changes",
                    "notes": "This is just for testing.",
                    "end_date": "2025-05-03",
                    "consultation_url": "https://example.com/consultation"
                },
                "seats_total": null,
                "division_election_sub_type": "",
                "division_subtype": "",
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
            "metadata": null,
            "deleted": false,
            "cancelled": false,
            "replaces": null,
            "replaced_by": null,
            "tags": {"FOO":{"bar":"baz"}}
        }
        """
        )

        resp = self.client.get("/api/elections/")
        data = resp.json()
        self.assertEqual(data["results"][0], self.expected_object)

        resp = self.client.get("/api/elections/local.place-name-0.2017-03-23/")
        data = resp.json()
        self.assertEqual(data, self.expected_object)

        resp = self.client.get(
            "/api/elections/local.place-name-0.2017-03-23/geo/",
            content_type="application/json",
        )
        data = resp.json()
        self.assertEqual(data["properties"], self.expected_object)
