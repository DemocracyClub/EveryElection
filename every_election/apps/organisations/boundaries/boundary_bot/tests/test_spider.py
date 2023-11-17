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
            "slug": "gateshead",
            "latest_event": "Consultation on warding arrangements",
            "shapefiles": None,
            "eco": None,
            "eco_made": 0,
        },
        {
            "slug": "babergh",
            "latest_event": "The Babergh (Electoral Changes) Order 2017",
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
            "babergh": base_data["babergh"].copy(),
            "gateshead": base_data["gateshead"].copy(),
        }
        scraper.attach_spider_data()
        self.assertEqual(
            "The Babergh (Electoral Changes) Order 2017",
            scraper.data["babergh"]["latest_event"],
        )
        self.assertEqual(
            "http://www.lgbce.org.uk/__data/assets/file/derpderp.zip",
            scraper.data["babergh"]["shapefiles"],
        )
        self.assertEqual(
            "http://legislation.gov.uk/foo/bar/derpderp/made",
            scraper.data["babergh"]["eco"],
        )
        self.assertEqual(1, scraper.data["babergh"]["eco_made"])
        self.assertEqual(
            "Consultation on warding arrangements",
            scraper.data["gateshead"]["latest_event"],
        )
        self.assertIsNone(scraper.data["gateshead"]["shapefiles"])
        self.assertEqual(0, scraper.data["gateshead"]["eco_made"])

    @mock.patch(
        "organisations.boundaries.boundary_bot.scraper.SpiderWrapper.run_spider",
        mock_run_spider,
    )
    def test_unexpected(self):
        scraper = LgbceScraper(False, False)
        scraper.data = {
            "babergh": base_data["babergh"].copy(),
        }
        with self.assertRaises(ScraperException):
            scraper.attach_spider_data()
