import os
from unittest import mock

from data_provider import base_data
from django.test import TestCase
from organisations.boundaries.boundary_bot.scraper import (
    LgbceScraper,
    ScraperException,
)


@mock.patch(
    "organisations.boundaries.boundary_bot.code_matcher.CodeMatcher.get_data",
    lambda x: [],
)
class IndexParserTests(TestCase):
    def get_fixture(self, fixture):
        dirname = os.path.dirname(os.path.abspath(__file__))
        fixture_path = os.path.abspath(os.path.join(dirname, fixture))
        with open(fixture_path, "r") as f:
            return f.read()

    def test_parse_valid(self):
        scraper = LgbceScraper(False, False)
        fixture = self.get_fixture("fixtures/index/valid.html")
        scraper.parse_index(fixture)
        self.assertEqual(22, len(scraper.data))
        self.assertDictEqual(base_data["babergh"], scraper.data["babergh"])
        self.assertDictEqual(
            base_data["calderdale"], scraper.data["calderdale"]
        )
        self.assertDictEqual(base_data["allerdale"], scraper.data["allerdale"])
        self.assertDictEqual(base_data["ealing"], scraper.data["ealing"])

    def test_parse_unexpected_heading(self):
        scraper = LgbceScraper(False, False)
        fixture = self.get_fixture("fixtures/index/unexpected_heading.html")
        with self.assertRaises(ScraperException):
            scraper.parse_index(fixture)

    def test_parse_missing_heading(self):
        scraper = LgbceScraper(False, False)
        fixture = self.get_fixture("fixtures/index/missing_heading.html")
        with self.assertRaises(ScraperException):
            scraper.parse_index(fixture)
