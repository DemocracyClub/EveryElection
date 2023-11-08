import scraperwiki
from unittest import mock, TestCase
from boundary_bot.scraper import LgbceScraper
from data_provider import base_data


@mock.patch("boundary_bot.code_matcher.CodeMatcher.get_data", lambda x: [])
class NotificationTests(TestCase):
    def setUp(self):
        scraperwiki.sqlite.execute("DROP TABLE IF EXISTS lgbce_reviews;")

    def test_no_events(self):
        scraper = LgbceScraper(False, False)
        scraper.data = {
            "babergh": base_data["babergh"].copy(),
        }
        scraper.data["babergh"]["latest_event"] = "foo"
        scraper.save()
        scraper.make_notifications()
        self.assertEqual(0, len(scraper.slack_helper.messages))
        self.assertEqual(0, len(scraper.github_helper.issues))

    def test_new_record(self):
        scraper = LgbceScraper(False, False)
        scraper.data = {
            "babergh": base_data["babergh"].copy(),
        }
        scraper.data["babergh"]["latest_event"] = "foo"
        scraper.make_notifications()
        self.assertEqual(1, len(scraper.slack_helper.messages))
        assert "New boundary review found" in scraper.slack_helper.messages[0]
        self.assertEqual(0, len(scraper.github_helper.issues))

    def test_new_event(self):
        scraper = LgbceScraper(False, False)
        scraper.data = {
            "babergh": base_data["babergh"].copy(),
        }
        scraper.data["babergh"]["latest_event"] = "foo"
        scraper.save()
        scraper.data["babergh"]["latest_event"] = "bar"
        scraper.make_notifications()
        self.assertEqual(1, len(scraper.slack_helper.messages))
        assert (
            "boundary review status updated to 'bar'"
            in scraper.slack_helper.messages[0]
        )
        self.assertEqual(0, len(scraper.github_helper.issues))

    def test_eco_made(self):
        scraper = LgbceScraper(False, False)
        scraper.data = {
            "allerdale": base_data["allerdale"].copy(),
        }
        scraper.data["allerdale"][
            "latest_event"
        ] = "The Allerdale Electoral Changes order"
        scraper.data["allerdale"]["status"] = "Current Reviews"
        scraper.save()
        scraper.data["allerdale"]["status"] = "Recent Reviews"
        scraper.make_notifications()
        self.assertEqual(1, len(scraper.slack_helper.messages))
        assert "Completed boundary review" in scraper.slack_helper.messages[0]
        self.assertEqual(1, len(scraper.github_helper.issues))
        assert (
            "Completed boundary review"
            in scraper.github_helper.issues[0]["title"]
        )
        assert (
            "Completed boundary review"
            in scraper.github_helper.issues[0]["body"]
        )
