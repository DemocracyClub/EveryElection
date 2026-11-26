from datetime import date
from unittest.mock import patch

from django.test import override_settings
from freezegun import freeze_time
from organisations.tests.factories import (
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
    OrganisationFactory,
)
from rest_framework.test import APITestCase

ORG_URL = "/api/organisations/local-authority/TEST1/2016-10-01"
SP_ORG_URL = "/api/organisations/sp/sp/1999-05-06"
HOST = "http://testserver"


class DivisionSetAPITestCase(APITestCase):
    """
    A local authority (TEST1) with three consecutive division sets:
        old:     2016-10-01 to 2019-05-01
        current: 2019-05-02 to 2027-05-05
        future:  2027-05-06 onwards


    The Scottish Parliament (sp) with one division set, starting
    2011-05-05, which has divisions of two types:
        constituencies (SPC)
        regions (SPE).
    """

    @classmethod
    def setUpTestData(cls):
        cls.org = OrganisationFactory(
            official_identifier="TEST1",
            organisation_type="local-authority",
            common_name="Test One",
            start_date=date(2016, 10, 1),
            end_date=None,
        )
        cls.old_divset = OrganisationDivisionSetFactory(
            organisation=cls.org,
            start_date="2016-10-01",
            end_date="2019-05-01",
            short_title="Old divisions",
        )
        cls.current_divset = OrganisationDivisionSetFactory(
            organisation=cls.org,
            start_date="2019-05-02",
            end_date="2027-05-05",
            short_title="Current divisions",
        )
        cls.future_divset = OrganisationDivisionSetFactory(
            organisation=cls.org,
            start_date="2027-05-06",
            end_date=None,
            short_title="Future divisions",
        )
        for name in ["Ward B", "Ward A"]:
            OrganisationDivisionFactory(
                divisionset=cls.current_divset,
                name=name,
                division_type="DIW",
            )

        cls.sp_org = OrganisationFactory(
            official_identifier="sp",
            organisation_type="sp",
            common_name="Scottish Parliament",
            start_date=date(1999, 5, 6),
            end_date=None,
        )
        cls.sp_divset = OrganisationDivisionSetFactory(
            organisation=cls.sp_org,
            start_date="2011-05-05",
            end_date=None,
            short_title="Scottish Parliament divisions",
        )
        for name, division_type in [
            ("Glasgow Kelvin", "SPC"),
            ("Edinburgh Central", "SPC"),
            ("Lothian", "SPE"),
        ]:
            OrganisationDivisionFactory(
                divisionset=cls.sp_divset,
                name=name,
                division_type=division_type,
            )


class TestDivisionSetDetail(DivisionSetAPITestCase):
    def test_detail(self):
        resp = self.client.get(f"{ORG_URL}/division_sets/2019-05-02/")
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertEqual(
            [
                "url",
                "start_date",
                "end_date",
                "short_title",
                "legislation_url",
                "consultation_url",
                "notes",
                "last_modified",
                "division_types",
                "previous",
                "next",
                "pmtiles_url",
                "divisions",
            ],
            list(data.keys()),
        )
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2019-05-02/", data["url"]
        )
        self.assertEqual("2019-05-02", data["start_date"])
        self.assertEqual("2027-05-05", data["end_date"])
        self.assertEqual("Current divisions", data["short_title"])
        self.assertEqual(["DIW"], data["division_types"])
        self.assertEqual(
            ["Ward A", "Ward B"],
            [division["name"] for division in data["divisions"]],
        )
        self.assertEqual(
            [
                "name",
                "official_identifier",
                "slug",
                "division_type",
                "division_subtype",
                "division_election_sub_type",
                "seats_total",
                "territory_code",
                "created",
                "modified",
            ],
            list(data["divisions"][0].keys()),
        )

    def test_previous_and_next(self):
        data = self.client.get(f"{ORG_URL}/division_sets/2019-05-02/").json()
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2016-10-01/", data["previous"]
        )
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2027-05-06/", data["next"]
        )

    def test_previous_and_next_at_ends(self):
        first = self.client.get(f"{ORG_URL}/division_sets/2016-10-01/").json()
        self.assertIsNone(first["previous"])
        self.assertIsNotNone(first["next"])
        last = self.client.get(f"{ORG_URL}/division_sets/2027-05-06/").json()
        self.assertIsNotNone(last["previous"])
        self.assertIsNone(last["next"])

    def test_previous_and_next_ignore_other_organisations(self):
        OrganisationDivisionSetFactory(
            organisation=OrganisationFactory(official_identifier="TEST2"),
            start_date="2000-01-01",
            end_date=None,
        )
        first = self.client.get(f"{ORG_URL}/division_sets/2016-10-01/").json()
        self.assertIsNone(first["previous"])

    def test_format_suffix(self):
        resp = self.client.get(f"{ORG_URL}/division_sets/2019-05-02.json")
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2019-05-02.json", data["url"]
        )
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2027-05-06.json", data["next"]
        )

    def test_dates_match_within_lifetime(self):
        """
        Neither date in the URL has to be a start date, but the URLs in
        the response always use the start dates.
        """
        resp = self.client.get(
            "/api/organisations/local-authority/TEST1/2024-01-01/division_sets/2025-06-15/"
        )
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertEqual("Current divisions", data["short_title"])
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2019-05-02/", data["url"]
        )

    def test_end_date_is_inclusive(self):
        data = self.client.get(f"{ORG_URL}/division_sets/2027-05-05/").json()
        self.assertEqual("Current divisions", data["short_title"])

    def test_open_ended_division_set(self):
        data = self.client.get(f"{ORG_URL}/division_sets/2099-01-01/").json()
        self.assertEqual("Future divisions", data["short_title"])

    def test_date_before_first_division_set_not_found(self):
        resp = self.client.get(f"{ORG_URL}/division_sets/2001-01-01/")
        self.assertEqual(404, resp.status_code)

    def test_organisation_not_found(self):
        resp = self.client.get(
            "/api/organisations/local-authority/NOPE/2016-10-01/division_sets/2019-05-02/"
        )
        self.assertEqual(404, resp.status_code)

    def test_impossible_dates_not_found(self):
        # Each request uses a different date so the message shows which
        # URL segment was rejected.
        resp = self.client.get(f"{ORG_URL}/division_sets/2019-13-45/")
        self.assertEqual(404, resp.status_code)
        self.assertEqual(
            "'2019-13-45' is not a valid yyyy-mm-dd date", resp.json()["detail"]
        )
        resp = self.client.get(
            "/api/organisations/local-authority/TEST1/2016-02-30/division_sets/2019-05-02/"
        )
        self.assertEqual(404, resp.status_code)
        self.assertEqual(
            "'2016-02-30' is not a valid yyyy-mm-dd date", resp.json()["detail"]
        )

    def test_provisional_organisation_not_found(self):
        org = OrganisationFactory(official_identifier="PROV", provisional=True)
        OrganisationDivisionSetFactory(
            organisation=org, start_date="2017-01-01", end_date=None
        )
        resp = self.client.get(
            "/api/organisations/local-authority/PROV/2016-10-01/division_sets/2017-01-01/"
        )
        self.assertEqual(404, resp.status_code)

    def test_multiple_division_types(self):
        data = self.client.get(f"{SP_ORG_URL}/division_sets/2011-05-05/").json()
        self.assertEqual(["SPC", "SPE"], data["division_types"])
        self.assertEqual(
            ["Edinburgh Central", "Glasgow Kelvin", "Lothian"],
            [division["name"] for division in data["divisions"]],
        )

    def test_filter_divisions_by_type(self):
        data = self.client.get(
            f"{SP_ORG_URL}/division_sets/2011-05-05/?division_type=SPC"
        ).json()
        self.assertEqual(
            ["Edinburgh Central", "Glasgow Kelvin"],
            [division["name"] for division in data["divisions"]],
        )
        # division_types describes the whole division set
        self.assertEqual(["SPC", "SPE"], data["division_types"])

    def test_filter_divisions_by_type_no_match(self):
        resp = self.client.get(
            f"{ORG_URL}/division_sets/2019-05-02/?division_type=nope"
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual([], resp.json()["divisions"])

    def test_query_count(self):
        # organisation, division set, division types, previous, next,
        # divisions
        with self.assertNumQueries(6):
            self.client.get(f"{ORG_URL}/division_sets/2019-05-02/")


SUMMARY_FIELDS = [
    "url",
    "start_date",
    "end_date",
    "short_title",
    "legislation_url",
    "consultation_url",
    "notes",
    "last_modified",
]


class TestDivisionSetOrganisationList(DivisionSetAPITestCase):
    def test_list(self):
        # A division set belonging to a different organisation,
        # which should not be listed
        OrganisationDivisionSetFactory(
            organisation=OrganisationFactory(official_identifier="TEST2")
        )

        resp = self.client.get(f"{ORG_URL}/division_sets/")
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertEqual(
            ["count", "next", "previous", "results"], list(data.keys())
        )
        self.assertEqual(3, data["count"])
        self.assertEqual(
            ["Future divisions", "Current divisions", "Old divisions"],
            [result["short_title"] for result in data["results"]],
        )
        self.assertEqual(SUMMARY_FIELDS, list(data["results"][0].keys()))
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2027-05-06/",
            data["results"][0]["url"],
        )

    def test_format_suffix(self):
        resp = self.client.get(f"{ORG_URL}/division_sets.json")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(3, resp.json()["count"])

    def test_organisation_date_matches_within_lifetime(self):
        resp = self.client.get(
            "/api/organisations/local-authority/TEST1/2024-01-01/division_sets/"
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(3, resp.json()["count"])

    def test_only_lists_one_generation_of_an_organisation(self):
        self.org.end_date = date(2030, 1, 1)
        self.org.save()
        self.future_divset.end_date = date(2030, 1, 1)
        self.future_divset.save()
        next_generation = OrganisationFactory(
            official_identifier="TEST1",
            organisation_type="local-authority",
            start_date=date(2030, 1, 2),
        )
        OrganisationDivisionSetFactory(
            organisation=next_generation,
            start_date="2030-01-02",
            end_date=None,
            short_title="Next generation divisions",
        )
        data = self.client.get(
            "/api/organisations/local-authority/TEST1/2030-01-02/division_sets/"
        ).json()
        self.assertEqual(
            ["Next generation divisions"],
            [result["short_title"] for result in data["results"]],
        )

    def test_organisation_without_division_sets(self):
        OrganisationFactory(official_identifier="TEST2")
        resp = self.client.get(
            "/api/organisations/local-authority/TEST2/2016-10-01/division_sets/"
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual([], resp.json()["results"])

    def test_organisation_not_found(self):
        resp = self.client.get(
            "/api/organisations/local-authority/NOPE/2016-10-01/division_sets/"
        )
        self.assertEqual(404, resp.status_code)

    def test_provisional_organisation_not_found(self):
        OrganisationFactory(official_identifier="PROV", provisional=True)
        resp = self.client.get(
            "/api/organisations/local-authority/PROV/2016-10-01/division_sets/"
        )
        self.assertEqual(404, resp.status_code)

    def test_query_count(self):
        # organisation, count, division sets
        with self.assertNumQueries(3):
            self.client.get(f"{ORG_URL}/division_sets/")


@freeze_time("2026-11-12")
class TestDivisionSetList(DivisionSetAPITestCase):
    """
    On the frozen date:
        ended:       "Old divisions" (TEST1)
        active:      "Current divisions" (TEST1), "Constituencies" (parl),
                     "Scottish Parliament divisions" (sp)
        not started: "Future divisions" (TEST1)
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.parl = OrganisationFactory(
            official_identifier="parl-hoc",
            organisation_type="parl",
            common_name="House of Commons",
        )
        cls.parl_divset = OrganisationDivisionSetFactory(
            organisation=cls.parl,
            start_date="2024-07-04",
            end_date=None,
            short_title="Constituencies",
        )

    def get_titles(self, query=""):
        resp = self.client.get(f"/api/division_sets/{query}")
        self.assertEqual(200, resp.status_code, resp.content)
        data = resp.json()
        self.assertEqual(data["count"], len(data["results"]))
        return [result["short_title"] for result in data["results"]]

    def test_list(self):
        resp = self.client.get("/api/division_sets/")
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertEqual(
            ["count", "next", "previous", "results"], list(data.keys())
        )
        self.assertEqual(5, data["count"])
        self.assertEqual(
            [
                "Future divisions",
                "Constituencies",
                "Current divisions",
                "Old divisions",
                "Scottish Parliament divisions",
            ],
            [result["short_title"] for result in data["results"]],
        )
        self.assertEqual(SUMMARY_FIELDS, list(data["results"][0].keys()))
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2027-05-06/",
            data["results"][0]["url"],
        )

    def test_format_suffix(self):
        resp = self.client.get("/api/division_sets.json")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(5, resp.json()["count"])

    def test_listed_in_api_root(self):
        data = self.client.get("/api/").json()
        self.assertEqual(f"{HOST}/api/division_sets/", data["division_sets"])

    def test_no_route_by_primary_key(self):
        resp = self.client.get(f"/api/division_sets/{self.parl_divset.pk}/")
        self.assertEqual(404, resp.status_code)

    def test_pagination(self):
        data = self.client.get("/api/division_sets/?limit=3").json()
        self.assertEqual(5, data["count"])
        self.assertEqual(3, len(data["results"]))
        self.assertIsNotNone(data["next"])

    def test_excludes_provisional_organisations(self):
        OrganisationDivisionSetFactory(
            organisation=OrganisationFactory(
                official_identifier="PROV", provisional=True
            ),
            short_title="Provisional organisation divisions",
        )
        self.assertNotIn(
            "Provisional organisation divisions", self.get_titles()
        )

    def test_filter_date(self):
        self.assertEqual(
            ["Old divisions", "Scottish Parliament divisions"],
            self.get_titles("?date=2018-01-01"),
        )
        self.assertEqual(
            [
                "Future divisions",
                "Constituencies",
                "Scottish Parliament divisions",
            ],
            self.get_titles("?date=2028-01-01"),
        )

    def test_filter_date_invalid(self):
        resp = self.client.get("/api/division_sets/?date=yesterday")
        self.assertEqual(400, resp.status_code)
        self.assertIn("date", resp.json())

    def test_filter_active(self):
        # Django parses `?active` and `?active=` the same way
        for query in ("?active", "?active="):
            with self.subTest(query=query):
                self.assertEqual(
                    [
                        "Constituencies",
                        "Current divisions",
                        "Scottish Parliament divisions",
                    ],
                    self.get_titles(query),
                )

    def test_filter_future(self):
        for query in ("?future", "?future="):
            with self.subTest(query=query):
                self.assertEqual(["Future divisions"], self.get_titles(query))

    def test_flags_reject_values(self):
        for param in ("active", "future"):
            for value in ("true", "1", "false", "0", "maybe"):
                with self.subTest(param=param, value=value):
                    resp = self.client.get(
                        f"/api/division_sets/?{param}={value}"
                    )
                    self.assertEqual(400, resp.status_code)
                    (message,) = resp.json()[param]
                    self.assertIn("doesn't take a value", message)

    def test_flags_not_in_browsable_api_filter_form(self):
        """
        The filter form submits every input, including empty ones, and
        an empty value turns a flag on.
        """
        resp = self.client.get("/api/division_sets/", HTTP_ACCEPT="text/html")
        self.assertEqual(200, resp.status_code)
        # The form is there, with the other filters in it
        self.assertContains(resp, 'name="date"')
        for param in ("active", "future"):
            with self.subTest(param=param):
                self.assertNotContains(resp, f'name="{param}"')

    def test_date_filters_are_mutually_exclusive(self):
        for query, names in [
            ("date=2026-11-12&active", "'date', 'active'"),
            ("date=2026-11-12&future", "'date', 'future'"),
            ("active&future", "'active', 'future'"),
            ("date=2026-11-12&active&future", "'date', 'active', 'future'"),
        ]:
            with self.subTest(query=query):
                resp = self.client.get(f"/api/division_sets/?{query}")
                self.assertEqual(400, resp.status_code)
                (message,) = resp.json()["__all__"]
                self.assertIn(
                    "Only one of 'date', 'active' and 'future'", message
                )
                self.assertTrue(message.endswith(names), message)

    def test_empty_date_is_ignored(self):
        self.assertEqual(
            [
                "Constituencies",
                "Current divisions",
                "Scottish Parliament divisions",
            ],
            self.get_titles("?active&date="),
        )

    def test_filter_organisation_type(self):
        self.assertEqual(
            ["Constituencies"], self.get_titles("?organisation_type=parl")
        )

    def test_filter_organisation_type_rejects_unknown_values(self):
        resp = self.client.get("/api/division_sets/?organisation_type=nope")
        self.assertEqual(400, resp.status_code)
        (message,) = resp.json()["organisation_type"]
        self.assertIn("Select a valid choice", message)

    def test_organisation_type_is_dropdown_in_browsable_api(self):
        resp = self.client.get("/api/division_sets/", HTTP_ACCEPT="text/html")
        self.assertEqual(200, resp.status_code)
        self.assertContains(resp, '<select name="organisation_type"')
        self.assertContains(resp, '<option value="parl">parl</option>')

    def test_combined_filters(self):
        self.assertEqual(
            ["Current divisions"],
            self.get_titles("?active&organisation_type=local-authority"),
        )

    def test_query_count(self):
        # count, division sets
        with self.assertNumQueries(2):
            self.client.get("/api/division_sets/")


class TestDivisionSetPMTiles(DivisionSetAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.current_divset.pmtiles_md5_hash = "abc123"
        cls.current_divset.save()
        cls.file_name = f"{cls.org.slug}_{cls.current_divset.pk}_abc123.pmtiles"

    def test_detail_links_to_pmtiles_endpoint(self):
        data = self.client.get(f"{ORG_URL}/division_sets/2019-05-02/").json()
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2019-05-02/pmtiles/",
            data["pmtiles_url"],
        )

    def test_detail_pmtiles_url_has_no_format_suffix(self):
        data = self.client.get(
            f"{ORG_URL}/division_sets/2019-05-02.json"
        ).json()
        self.assertEqual(
            f"{HOST}{ORG_URL}/division_sets/2019-05-02/pmtiles/",
            data["pmtiles_url"],
        )

    def test_detail_pmtiles_url_null_without_hash(self):
        data = self.client.get(f"{ORG_URL}/division_sets/2016-10-01/").json()
        self.assertIsNone(data["pmtiles_url"])

    @override_settings(PUBLIC_DATA_BUCKET="test-bucket")
    def test_detail_does_not_check_file_exists(self):
        with patch("organisations.models.divisions.S3Wrapper") as s3_wrapper:
            self.client.get(f"{ORG_URL}/division_sets/2019-05-02/")
        s3_wrapper.assert_not_called()

    @override_settings(PUBLIC_DATA_BUCKET="test-bucket")
    def test_redirects_to_s3(self):
        with patch("organisations.models.divisions.S3Wrapper") as s3_wrapper:
            s3_wrapper.return_value.check_s3_obj_exists.return_value = True
            resp = self.client.get(
                f"{ORG_URL}/division_sets/2019-05-02/pmtiles/"
            )
        self.assertEqual(302, resp.status_code)
        self.assertEqual(
            f"https://s3.eu-west-2.amazonaws.com/test-bucket/pmtiles-store/{self.file_name}",
            resp["Location"],
        )

    @override_settings(PUBLIC_DATA_BUCKET="test-bucket")
    def test_not_found_when_file_missing_from_s3(self):
        with patch("organisations.models.divisions.S3Wrapper") as s3_wrapper:
            s3_wrapper.return_value.check_s3_obj_exists.return_value = False
            resp = self.client.get(
                f"{ORG_URL}/division_sets/2019-05-02/pmtiles/"
            )
        self.assertEqual(404, resp.status_code)

    @override_settings(PUBLIC_DATA_BUCKET=None)
    def test_redirects_to_local_file_view(self):
        with patch(
            "organisations.models.divisions.os.path.exists", return_value=True
        ) as exists:
            resp = self.client.get(
                f"{ORG_URL}/division_sets/2019-05-02/pmtiles/"
            )
        self.assertTrue(exists.call_args[0][0].endswith(self.file_name))
        self.assertEqual(302, resp.status_code)
        self.assertEqual(
            f"/organisations/boundaries/pmtiles/{self.current_divset.pk}/",
            resp["Location"],
        )

    @override_settings(PUBLIC_DATA_BUCKET=None)
    def test_not_found_when_local_file_missing(self):
        with patch(
            "organisations.models.divisions.os.path.exists", return_value=False
        ):
            resp = self.client.get(
                f"{ORG_URL}/division_sets/2019-05-02/pmtiles/"
            )
        self.assertEqual(404, resp.status_code)

    def test_not_found_without_hash(self):
        resp = self.client.get(f"{ORG_URL}/division_sets/2016-10-01/pmtiles/")
        self.assertEqual(404, resp.status_code)

    def test_division_set_not_found(self):
        resp = self.client.get(f"{ORG_URL}/division_sets/2001-01-01/pmtiles/")
        self.assertEqual(404, resp.status_code)

    @override_settings(PUBLIC_DATA_BUCKET="test-bucket")
    def test_date_matches_within_lifetime(self):
        with patch("organisations.models.divisions.S3Wrapper") as s3_wrapper:
            s3_wrapper.return_value.check_s3_obj_exists.return_value = True
            resp = self.client.get(
                f"{ORG_URL}/division_sets/2025-06-15/pmtiles/"
            )
        self.assertEqual(302, resp.status_code)
        self.assertIn(self.file_name, resp["Location"])


@freeze_time("2026-01-01")
class TestDivisionSetLastModified(DivisionSetAPITestCase):
    """
    Every object in the fixtures is saved on the frozen date. Each test
    saves one division of "Current divisions" on a later date, which
    should then be its division set's last_modified.
    """

    def save_a_current_division(self):
        with freeze_time("2026-02-01"):
            self.current_divset.divisions.first().save()

    def get_last_modified_by_title(self, url):
        results = self.client.get(url).json()["results"]
        return {r["short_title"]: r["last_modified"] for r in results}

    def test_detail(self):
        self.save_a_current_division()
        data = self.client.get(f"{ORG_URL}/division_sets/2019-05-02/").json()
        self.assertEqual("2026-02-01T00:00:00Z", data["last_modified"])

    def test_detail_without_divisions(self):
        data = self.client.get(f"{ORG_URL}/division_sets/2016-10-01/").json()
        self.assertEqual("2026-01-01T00:00:00Z", data["last_modified"])

    def test_organisation_list(self):
        self.save_a_current_division()
        self.assertEqual(
            {
                "Future divisions": "2026-01-01T00:00:00Z",
                "Current divisions": "2026-02-01T00:00:00Z",
                "Old divisions": "2026-01-01T00:00:00Z",
            },
            self.get_last_modified_by_title(f"{ORG_URL}/division_sets/"),
        )

    def test_list(self):
        self.save_a_current_division()
        self.assertEqual(
            {
                "Future divisions": "2026-01-01T00:00:00Z",
                "Current divisions": "2026-02-01T00:00:00Z",
                "Old divisions": "2026-01-01T00:00:00Z",
                "Scottish Parliament divisions": "2026-01-01T00:00:00Z",
            },
            self.get_last_modified_by_title("/api/division_sets/"),
        )

    def test_list_filter(self):
        self.save_a_current_division()
        resp = self.client.get(
            "/api/division_sets/?last_modified=2026-01-15T00:00:00Z"
        )
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        self.assertEqual(1, data["count"])
        self.assertEqual(
            ["Current divisions"],
            [result["short_title"] for result in data["results"]],
        )

    def test_list_filter_excludes_equal_timestamp(self):
        self.save_a_current_division()
        resp = self.client.get(
            "/api/division_sets/?last_modified=2026-02-01T00:00:00Z"
        )
        self.assertEqual(0, resp.json()["count"])

    def test_list_filter_combines_with_date_filters(self):
        self.save_a_current_division()
        resp = self.client.get(
            "/api/division_sets/?last_modified=2026-01-15T00:00:00Z&future"
        )
        self.assertEqual(0, resp.json()["count"])

    def test_list_filter_invalid(self):
        resp = self.client.get("/api/division_sets/?last_modified=nope")
        self.assertEqual(400, resp.status_code)
