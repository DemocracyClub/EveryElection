from unittest import mock

from data_provider import base_data
from django.test import TestCase
from organisations.boundaries.boundary_bot.scraper import (
    LgbceScraper,
    ScraperException,
)


def mock_run_spider(obj):
    return [
        {
            "slug": "fake_org_1",
            "latest_event": "Consultation on warding arrangements",
            "shapefiles": None,
            "eco": None,
            "eco_made": 0,
        },
        {
            "slug": "fake_org_2",
            "latest_event": "The fake_org_2 (Electoral Changes) Order 2017",
            "shapefiles": "http://www.lgbce.org.uk/__data/assets/file/derpderp.zip",
            "eco": "http://legislation.gov.uk/foo/bar/derpderp/made",
            "eco_made": 1,
        },
    ]


@mock.patch(
    "organisations.boundaries.boundary_bot.code_matcher.CodeMatcher.get_data",
    lambda x: [],
)
class AttachSpiderTests(TestCase):
    @mock.patch(
        "organisations.boundaries.boundary_bot.scraper.SpiderWrapper.run_spider",
        mock_run_spider,
    )
    def test_valid(self):
        scraper = LgbceScraper(False, False)
        scraper.data = {
            "fake_org_2": base_data["fake_org_2"].copy(),
            "fake_org_1": base_data["fake_org_1"].copy(),
        }
        scraper.attach_spider_data()
        self.assertEqual(
            "The fake_org_2 (Electoral Changes) Order 2017",
            scraper.data["fake_org_2"]["latest_event"],
        )
        self.assertEqual(
            "http://www.lgbce.org.uk/__data/assets/file/derpderp.zip",
            scraper.data["fake_org_2"]["shapefiles"],
        )
        self.assertEqual(
            "http://legislation.gov.uk/foo/bar/derpderp/made",
            scraper.data["fake_org_2"]["eco"],
        )
        self.assertEqual(1, scraper.data["fake_org_2"]["eco_made"])
        self.assertEqual(
            "Consultation on warding arrangements",
            scraper.data["fake_org_1"]["latest_event"],
        )
        self.assertIsNone(scraper.data["fake_org_1"]["shapefiles"])
        self.assertEqual(0, scraper.data["fake_org_1"]["eco_made"])

    @mock.patch(
        "organisations.boundaries.boundary_bot.scraper.SpiderWrapper.run_spider",
        mock_run_spider,
    )
    def test_unexpected(self):
        scraper = LgbceScraper(False, False)
        scraper.data = {
            "fake_org_2": base_data["fake_org_2"].copy(),
        }
        with self.assertRaises(ScraperException):
            scraper.attach_spider_data()
