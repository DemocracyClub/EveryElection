from unittest import mock

from data_provider import base_data
from django.test import TestCase
from organisations.boundaries.boundary_bot.scraper import LgbceScraper
from organisations.models.divisions import (
    OrganisationBoundaryReviewCorrectionSlip,
    ReviewStatus,
)
from organisations.tests.factories import (
    CompletedOrganisationBoundaryReviewFactory,
    IncompleteOrganisationBoundaryReviewFactory,
    OrganisationFactory,
)


@mock.patch(
    "organisations.boundaries.boundary_bot.code_matcher.CodeMatcher.get_data",
    lambda x: [],
)
class NotificationTests(TestCase):
    def setUp(self):
        super().setUp()
        self.babergh_org = OrganisationFactory(
            official_identifier="BAB", slug="babergh"
        )
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

    def test_notifications_for_new_correction_slips(self):
        existing_review = IncompleteOrganisationBoundaryReviewFactory(
            organisation=self.babergh_org
        )
        scraper = LgbceScraper(False, False)
        scraper.data = {
            "babergh": base_data["babergh"].copy(),
        }
        scraper.data["babergh"]["register_code"] = (
            self.babergh_org.official_identifier
        )
        scraper.data["babergh"]["status"] = existing_review.status
        scraper.data["babergh"]["latest_event"] = existing_review.latest_event
        scraper.data["babergh"]["boundaries_url"] = (
            existing_review.boundaries_url
        )
        scraper.data["babergh"]["correction_slips"] = [
            {
                "title": "Correction One",
                "url": "https://example.com/slip-one",
            },
            {
                "title": "Correction Two",
                "url": "https://example.com/slip-two",
            },
        ]
        scraper.make_notifications()
        self.assertEqual(2, len(scraper.slack_helper.messages))
        assert "New correction slip found" in scraper.slack_helper.messages[0]
        assert "New correction slip found" in scraper.slack_helper.messages[1]
        for slip, message in zip(
            scraper.data["babergh"]["correction_slips"],
            scraper.slack_helper.messages,
            strict=True,
        ):
            self.assertIn(slip["title"], message)
            self.assertIn(slip["url"], message)
        self.assertEqual(0, len(scraper.github_helper.issues))

    def test_no_notifications_for_existing_correction_slip(self):
        existing_review = IncompleteOrganisationBoundaryReviewFactory(
            organisation=self.babergh_org
        )
        scraper = LgbceScraper(False, False)
        scraper.data = {
            "babergh": base_data["babergh"].copy(),
        }
        scraper.data["babergh"]["register_code"] = (
            self.babergh_org.official_identifier
        )
        scraper.data["babergh"]["status"] = existing_review.status
        scraper.data["babergh"]["latest_event"] = existing_review.latest_event
        scraper.data["babergh"]["boundaries_url"] = (
            existing_review.boundaries_url
        )
        scraped_correction_slip = {
            "title": "Correction",
            "url": "https://example.com/slip",
        }
        scraper.data["babergh"]["correction_slips"] = [scraped_correction_slip]
        # Create existing slip record
        OrganisationBoundaryReviewCorrectionSlip(
            boundary_review=existing_review,
            legislation_title=scraped_correction_slip["title"],
            legislation_url=scraped_correction_slip["url"],
        ).save()

        scraper.make_notifications()

        self.assertEqual(0, len(scraper.slack_helper.messages))
        self.assertEqual(0, len(scraper.github_helper.issues))

    def test_notifications_for_correction_slip_on_new_review(self):
        scraper = LgbceScraper(False, False)
        scraper.data = {"babergh": base_data["babergh"].copy()}
        record = scraper.data["babergh"]
        record.update(
            register_code="BAB",
            latest_event="Some Event",
            status=ReviewStatus.CURRENT,
            correction_slips=[
                {"title": "Correction", "url": "https://example.com/slip"},
            ],
        )

        scraper.make_notifications()
        self.assertEqual(2, len(scraper.slack_helper.messages))
        self.assertIn(
            "https://example.com/slip", scraper.slack_helper.messages[1]
        )
        self.assertEqual(2, len(scraper.slack_helper.messages))
        self.assertEqual(0, len(scraper.github_helper.issues))

    def test_correction_slip_on_completed_review(self):
        review = CompletedOrganisationBoundaryReviewFactory(
            organisation=self.babergh_org
        )
        scraper = LgbceScraper(False, False)
        scraper.data = {"babergh": base_data["babergh"].copy()}
        scraper.data["babergh"].update(
            register_code="BAB",
            status=review.status,
            latest_event=review.latest_event,
            legislation_url=review.legislation_url,
            correction_slips=[
                {"title": "Correction", "url": "https://example.com/slip"},
            ],
        )

        scraper.make_notifications()
        self.assertEqual(1, len(scraper.slack_helper.messages))

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
