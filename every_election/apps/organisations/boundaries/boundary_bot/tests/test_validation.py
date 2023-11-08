import scraperwiki
from unittest import mock, TestCase
from boundary_bot.scraper import LgbceScraper, ScraperException
from data_provider import base_data


@mock.patch("boundary_bot.code_matcher.CodeMatcher.get_data", lambda x: [])
class ValidationTests(TestCase):
    def setUp(self):
        scraperwiki.sqlite.execute("DROP TABLE IF EXISTS lgbce_reviews;")

    def test_valid(self):
        scraper = LgbceScraper(False, False)
        scraper.data = {
            "babergh": base_data["babergh"].copy(),
        }
        scraper.data["babergh"]["latest_event"] = "foo"
        scraper.BOOTSTRAP_MODE = False
        self.assertTrue(scraper.validate())

    def test_null_event(self):
        # latest_event = None and we already have a non-empty latest_event in the DB
        scraper = LgbceScraper(False, False)
        scraper.data = {
            "babergh": base_data["babergh"].copy(),
        }
        scraper.data["babergh"]["latest_event"] = "foo"
        scraper.save()
        scraper.data["babergh"]["latest_event"] = None

        scraper.BOOTSTRAP_MODE = False
        with self.assertRaises(ScraperException) as e:
            scraper.validate()
        assert "Failed to populate 'latest_event' field" in str(e.exception)

    def test_new_completed(self):
        # status = 'Recent Reviews' and record not in DB
        scraper = LgbceScraper(False, False)
        scraper.data = {
            "allerdale": base_data["allerdale"].copy(),
        }
        scraper.data["allerdale"][
            "latest_event"
        ] = "The Allerdale Electoral Change order"
        scraper.data["allerdale"]["eco_made"] = 1

        scraper.BOOTSTRAP_MODE = False
        with self.assertRaises(ScraperException) as e:
            scraper.validate()
        assert "New record found but status is 'Recent Reviews'" in str(
            e.exception
        )

        # this check should be skipped in bootstrap mode
        scraper.BOOTSTRAP_MODE = True
        self.assertTrue(scraper.validate())

    def test_backwards_status_move(self):
        # old status is 'Recent Reviews', new status is 'Current Reviews'
        scraper = LgbceScraper(False, False)
        scraper.data = {
            "allerdale": base_data["allerdale"].copy(),
        }
        scraper.data["allerdale"][
            "latest_event"
        ] = "The Allerdale Electoral Change order"
        scraper.data["allerdale"]["eco_made"] = 1
        scraper.save()
        scraper.data["allerdale"]["status"] = scraper.CURRENT_LABEL

        scraper.BOOTSTRAP_MODE = False
        with self.assertRaises(ScraperException) as e:
            scraper.validate()
        assert (
            "Record status has changed from 'Recent Reviews' to 'Current Reviews'"
            in str(e.exception)
        )

        # this check should be skipped in bootstrap mode
        scraper.BOOTSTRAP_MODE = True
        self.assertTrue(scraper.validate())

    def test_backwards_made_eco_move(self):
        # old eco_made value is 1, new value is 0
        scraper = LgbceScraper(False, False)
        scraper.data = {
            "allerdale": base_data["allerdale"].copy(),
        }
        scraper.data["allerdale"][
            "latest_event"
        ] = "The Allerdale Electoral Change order"
        scraper.data["allerdale"]["eco_made"] = 1
        scraper.data["allerdale"]["status"] = scraper.CURRENT_LABEL
        scraper.save()
        scraper.data["allerdale"]["eco_made"] = 0

        scraper.BOOTSTRAP_MODE = False
        with self.assertRaises(ScraperException) as e:
            scraper.validate()
        assert "'eco_made' field has changed from 1 to 0" in str(e.exception)

        # this check should be skipped in bootstrap mode
        scraper.BOOTSTRAP_MODE = True
        self.assertTrue(scraper.validate())
