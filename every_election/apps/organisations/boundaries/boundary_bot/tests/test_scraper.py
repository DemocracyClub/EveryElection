from data_provider import base_data
from django.test import TestCase
from mock import mock
from organisations.boundaries.boundary_bot.scraper import (
    LgbceScraper,
    ScraperException,
)
from organisations.models.divisions import (
    EditStatus,
    OrganisationBoundaryReview,
    ReviewStatus,
)
from organisations.tests.factories import (
    CompletedOrganisationBoundaryReviewFactory,
    IncompleteOrganisationBoundaryReviewFactory,
    OrganisationFactory,
)


class TestScraper(TestCase):
    def setUp(self):
        self.scraper = LgbceScraper(False, False)

    def test_get_review_from_db_duplicate_title(self):
        org1 = OrganisationFactory()
        CompletedOrganisationBoundaryReviewFactory(
            organisation=org1,
            legislation_title="complete review - duplicate title",
        )
        CompletedOrganisationBoundaryReviewFactory(
            organisation=org1,
            legislation_title="complete review - duplicate title",
        )
        with self.assertRaises(ScraperException):
            self.scraper.get_review_from_db(
                {
                    "register_code": org1.official_identifier,
                    "legislation_title": "complete review - duplicate title",
                    "slug": org1.slug,
                }
            )

    def test_get_review_from_db(self):
        org1 = OrganisationFactory()
        complete_br = CompletedOrganisationBoundaryReviewFactory(
            organisation=org1, legislation_title="completed title"
        )
        incomplete_br = IncompleteOrganisationBoundaryReviewFactory(
            organisation=org1, legislation_title="uncompleted title"
        )
        comlete_qs = self.scraper.get_review_from_db(
            {
                "register_code": org1.official_identifier,
                "legislation_title": "completed title",
                "slug": org1.slug,
            }
        )
        incomlete_qs = self.scraper.get_review_from_db(
            {
                "register_code": org1.official_identifier,
                "legislation_title": "uncompleted title",
                "slug": org1.slug,
            }
        )
        self.assertEqual(1, len(comlete_qs))
        self.assertEqual(
            complete_br,
            comlete_qs[0],
        )
        self.assertEqual(1, len(incomlete_qs))
        self.assertEqual(
            incomplete_br,
            incomlete_qs[0],
        )

    def test_get_review_from_db_no_title(self):
        org1 = OrganisationFactory()
        CompletedOrganisationBoundaryReviewFactory(
            organisation=org1,
        )
        incomplete_br = IncompleteOrganisationBoundaryReviewFactory(
            organisation=org1,
        )
        qs = self.scraper.get_review_from_db(
            {
                "register_code": org1.official_identifier,
                "legislation_title": None,
                "slug": org1.slug,
            }
        )
        self.assertEqual(1, len(qs))
        self.assertEqual(
            incomplete_br,
            qs[0],
        )


@mock.patch(
    "organisations.boundaries.boundary_bot.code_matcher.CodeMatcher.get_data",
    lambda x: [],
)
class TestScraperSaves(TestCase):
    def setUp(self):
        self.scraper = LgbceScraper(False, False)
        self.allerdale_org = OrganisationFactory(
            official_identifier="ALL", slug="allerdale"
        )
        self.scraper.data = {
            "allerdale": base_data["allerdale"].copy(),
        }
        self.scraper.data["allerdale"]["register_code"] = "ALL"

    def test_save_new_review(self):
        self.assertEqual(0, len(OrganisationBoundaryReview.objects.all()))
        self.scraper.data["allerdale"]["latest_event"] = "Initial Consultation"
        self.scraper.data["allerdale"]["status"] = ReviewStatus.CURRENT

        with self.assertNumQueries(4):
            self.scraper.save()

        self.assertEqual(1, len(OrganisationBoundaryReview.objects.all()))

    def test_save_nothing_changed(self):
        IncompleteOrganisationBoundaryReviewFactory(
            organisation=self.allerdale_org, latest_event="Initial Consultation"
        )
        self.assertEqual(1, len(OrganisationBoundaryReview.objects.all()))
        self.assertEqual(
            "Initial Consultation",
            OrganisationBoundaryReview.objects.get(
                slug="allerdale"
            ).latest_event,
        )
        self.scraper.data["allerdale"]["latest_event"] = "Initial Consultation"
        self.scraper.data["allerdale"]["status"] = ReviewStatus.CURRENT

        with self.assertNumQueries(2):
            self.scraper.save()

        self.assertEqual(1, len(OrganisationBoundaryReview.objects.all()))
        self.assertEqual(
            "Initial Consultation",
            OrganisationBoundaryReview.objects.get(
                slug="allerdale"
            ).latest_event,
        )

    def test_save_updated_review(self):
        IncompleteOrganisationBoundaryReviewFactory(
            organisation=self.allerdale_org,
            latest_event="Initial Consultation",
        )
        self.assertEqual(1, len(OrganisationBoundaryReview.objects.all()))
        self.assertEqual(
            "Initial Consultation",
            OrganisationBoundaryReview.objects.get(
                slug="allerdale"
            ).latest_event,
        )
        self.assertEqual(
            "",
            OrganisationBoundaryReview.objects.get(
                slug="allerdale"
            ).legislation_title,
        )
        self.scraper.data["allerdale"][
            "latest_event"
        ] = "Making our recommendation into law"
        self.scraper.data["allerdale"]["legislation_title"] = "test title"
        self.scraper.data["allerdale"]["status"] = ReviewStatus.CURRENT

        with self.assertNumQueries(5):
            self.scraper.save()

        self.assertEqual(1, len(OrganisationBoundaryReview.objects.all()))
        self.assertEqual(
            "Making our recommendation into law",
            OrganisationBoundaryReview.objects.get(
                slug="allerdale"
            ).latest_event,
        )
        self.assertEqual(
            "test title",
            OrganisationBoundaryReview.objects.get(
                slug="allerdale"
            ).legislation_title,
        )

    def test_save_locked_review(self):
        IncompleteOrganisationBoundaryReviewFactory(
            organisation=self.allerdale_org,
            latest_event="Initial Consultation",
            edit_status=EditStatus.LOCKED,
        )
        self.assertEqual(1, len(OrganisationBoundaryReview.objects.all()))
        self.assertEqual(
            "Initial Consultation",
            OrganisationBoundaryReview.objects.get(
                slug="allerdale"
            ).latest_event,
        )
        self.assertEqual(
            "",
            OrganisationBoundaryReview.objects.get(
                slug="allerdale"
            ).legislation_title,
        )
        self.scraper.data["allerdale"][
            "latest_event"
        ] = "Making our recommendation into law"
        self.scraper.data["allerdale"]["legislation_title"] = "test title"
        self.scraper.data["allerdale"]["status"] = ReviewStatus.CURRENT

        with self.assertNumQueries(3):
            self.scraper.save()

        self.assertEqual(1, len(OrganisationBoundaryReview.objects.all()))
        self.assertEqual(
            "Initial Consultation",
            OrganisationBoundaryReview.objects.get(
                slug="allerdale"
            ).latest_event,
        )
        self.assertEqual(
            "",
            OrganisationBoundaryReview.objects.get(
                slug="allerdale"
            ).legislation_title,
        )
