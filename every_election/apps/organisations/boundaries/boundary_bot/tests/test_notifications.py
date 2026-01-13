from unittest import mock

from data_provider import base_data
from django.test import TestCase
from organisations.boundaries.boundary_bot.scraper import LgbceScraper
from organisations.models.divisions import ReviewStatus
from organisations.tests.factories import OrganisationFactory


@mock.patch(
    "organisations.boundaries.boundary_bot.code_matcher.CodeMatcher.get_data",
    lambda x: [],
)
class NotificationTests(TestCase):
    def setUp(self):
        super().setUp()
        OrganisationFactory(official_identifier="BAB")
        OrganisationFactory(official_identifier="ALL")

    def test_no_events(self):
        scraper = LgbceScraper(False, False)
        scraper.data = {
            "babergh": base_data["babergh"].copy(),
        }
        scraper.data["babergh"]["register_code"] = "BAB"
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
        scraper.data["babergh"]["register_code"] = "BAB"
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
        scraper.data["babergh"]["register_code"] = "BAB"
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
        scraper.data["allerdale"]["register_code"] = "ALL"
        scraper.data["allerdale"]["latest_event"] = (
            "The Allerdale Electoral Changes order"
        )
        scraper.data["allerdale"]["status"] = ReviewStatus.CURRENT
        scraper.save()
        scraper.data["allerdale"]["status"] = ReviewStatus.COMPLETED
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

    def test_single_send_event_on_send_notifications(self):
        with mock.patch(
            "organisations.boundaries.boundary_bot.scraper.send_event"
        ) as mock_send_event:
            scraper = LgbceScraper(False, True)
            scraper.data = {
                "babergh": base_data["babergh"].copy(),
                "allerdale": base_data["allerdale"].copy(),
            }
            scraper.data["babergh"]["register_code"] = "BAB"
            scraper.data["babergh"]["latest_event"] = "foo"
            scraper.data["allerdale"]["register_code"] = "ALL"
            scraper.data["allerdale"]["latest_event"] = "bar"

            scraper.make_notifications()
            scraper.send_notifications()

            mock_send_event.assert_called_once()
