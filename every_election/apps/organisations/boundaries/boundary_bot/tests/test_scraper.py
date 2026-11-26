from unittest.mock import patch

from data_provider import base_data
from django.test import TestCase
from organisations.boundaries.boundary_bot.code_matcher import CodeMatcher
from organisations.boundaries.boundary_bot.scraper import (
    LgbceScraper,
    ScraperException,
)
from organisations.models.divisions import (
    EditStatus,
    OrganisationBoundaryReview,
    OrganisationBoundaryReviewCorrectionSlip,
    ReviewStatus,
)
from organisations.tests.factories import (
    CompletedOrganisationBoundaryReviewFactory,
    IncompleteOrganisationBoundaryReviewFactory,
    OrganisationFactory,
)


class MockedCodeMatcherMixin:
    def setUp(self):
        self.patcher = patch.object(CodeMatcher, "get_data", return_value=[])
        self.mock_get_data = self.patcher.start()
        self.addCleanup(self.patcher.stop)
        super().setUp()


class TestScraper(MockedCodeMatcherMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.scraper = LgbceScraper(False, False)

    def test_get_review_from_db_duplicate_link(self):
        org1 = OrganisationFactory()
        CompletedOrganisationBoundaryReviewFactory(
            organisation=org1,
            legislation_url="https://www.legislation.gov.uk/uksi/2016/1222/contents/made",
        )
        CompletedOrganisationBoundaryReviewFactory(
            organisation=org1,
            legislation_url="https://www.legislation.gov.uk/uksi/2016/1222/contents/made",
        )
        with self.assertRaises(ScraperException):
            self.scraper.get_review_from_db(
                {
                    "register_code": org1.official_identifier,
                    "legislation_title": "scraped title",
                    "legislation_url": "https://www.legislation.gov.uk/uksi/2016/1222/contents/made",
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
        complete_qs = self.scraper.get_review_from_db(
            {
                "register_code": org1.official_identifier,
                "legislation_title": "completed title",
                "legislation_url": "https://www.legislation.gov.uk/uksi/2023/1023/made",
                "slug": org1.slug,
            }
        )
        incomplete_qs = self.scraper.get_review_from_db(
            {
                "register_code": org1.official_identifier,
                "legislation_title": "uncompleted title",
                "legislation_url": "",
                "slug": org1.slug,
            }
        )

        self.assertEqual(1, len(complete_qs))
        self.assertEqual(
            complete_br,
            complete_qs[0],
        )
        self.assertEqual(1, len(incomplete_qs))
        self.assertEqual(
            incomplete_br,
            incomplete_qs[0],
        )

    def test_get_review_from_db_draft_url(self):
        org1 = OrganisationFactory()
        CompletedOrganisationBoundaryReviewFactory(
            organisation=org1,
        )
        incomplete_br = IncompleteOrganisationBoundaryReviewFactory(
            organisation=org1,
            legislation_url="https://www.legislation.gov.uk/ukdsi/2018/9780111173626/contents",
        )
        qs = self.scraper.get_review_from_db(
            {
                "register_code": org1.official_identifier,
                "legislation_url": "https://www.legislation.gov.uk/ukdsi/2018/9780111173626/contents",
                "slug": org1.slug,
            }
        )
        self.assertEqual(1, len(qs))
        self.assertEqual(
            incomplete_br,
            qs[0],
        )


class TestScraperSaves(MockedCodeMatcherMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.scraper = LgbceScraper(False, False)
        self.allerdale_org = OrganisationFactory(
            official_identifier="ALL", slug="allerdale"
        )
        self.scraper.data = {
            "allerdale": base_data["allerdale"].copy(),
        }
        self.scraper.data["allerdale"]["register_code"] = "ALL"

    def test_save_correction_slips_on_review_once(self):
        # Save initial review before corrections issued
        self.scraper.data["allerdale"].update(
            latest_event="Effective date",
            status=ReviewStatus.CURRENT,
            legislation_title="The Allerdale (Electoral Changes) Order 2026",
        )

        self.scraper.save()
        # Save review with corrections
        self.scraper.data["allerdale"].update(
            latest_event="Effective date",
            status=ReviewStatus.CURRENT,
            correction_slips=[
                {"title": "Correction one", "url": "https://example.com/1"},
                {"title": "Correction two", "url": "https://example.com/2"},
            ],
        )
        self.scraper.save()
        # Save review with corrections again
        self.scraper.save()

        review = OrganisationBoundaryReview.objects.get(slug="allerdale")
        self.assertEqual(
            2,
            OrganisationBoundaryReviewCorrectionSlip.objects.filter(
                boundary_review=review
            ).count(),
        )

    def test_save_correction_slip_on_locked_review(self):
        completed = CompletedOrganisationBoundaryReviewFactory(
            organisation=self.allerdale_org,
            edit_status=EditStatus.LOCKED,
            latest_event="Effective Date",
        )
        self.scraper.data["allerdale"].update(
            legislation_url=completed.legislation_url,
            latest_event="Updated event",
            correction_slips=[
                {"title": "Correction", "url": "https://example.com/slip"},
            ],
        )

        self.scraper.save()
        completed.refresh_from_db()
        self.assertEqual("Effective Date", completed.latest_event)
        slip = OrganisationBoundaryReviewCorrectionSlip.objects.get()
        self.assertEqual(completed, slip.boundary_review)

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
        self.scraper.data["allerdale"]["latest_event"] = (
            "Making our recommendation into law"
        )
        self.scraper.data["allerdale"]["legislation_title"] = "test title"
        self.scraper.data["allerdale"]["status"] = ReviewStatus.CURRENT

        with self.assertNumQueries(4):
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
        self.scraper.data["allerdale"]["latest_event"] = (
            "Making our recommendation into law"
        )
        self.scraper.data["allerdale"]["legislation_title"] = "test title"
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
        self.assertEqual(
            "",
            OrganisationBoundaryReview.objects.get(
                slug="allerdale"
            ).legislation_title,
        )


class TestGetLegislationYear(MockedCodeMatcherMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.scraper = LgbceScraper(False, False)

    def test_get_legislation_year_uksi_url(self):
        legislation_url = "https://www.legislation.gov.uk/uksi/2023/1023/made"
        year = self.scraper.get_legislation_year(legislation_url)
        self.assertEqual(year, "2023")

    def test_get_legislation_year_uksi_url_with_id(self):
        legislation_url = "http://www.legislation.gov.uk/id/uksi/2023/732"
        year = self.scraper.get_legislation_year(legislation_url)
        self.assertEqual(year, "2023")

    def test_get_legislation_year_no_subdomain(self):
        legislation_url = "legislation.gov.uk/id/uksi/2023/732"
        year = self.scraper.get_legislation_year(legislation_url)
        self.assertEqual(year, "2023")

    def test_get_legislation_year_ukdsi_url(self):
        legislation_url = (
            "https://www.legislation.gov.uk/ukdsi/2024/9780348262735/contents"
        )
        year = self.scraper.get_legislation_year(legislation_url)
        self.assertEqual(year, "2024")

    def test_get_legislation_year_ukpga_url(self):
        legislation_url = (
            "https://www.legislation.gov.uk/ukpga/1999/29/contents"
        )
        year = self.scraper.get_legislation_year(legislation_url)
        self.assertEqual(year, "1999")

    def test_get_legislation_year_wsi_url(self):
        legislation_url = (
            "https://www.legislation.gov.uk/wsi/2021/1081/contents/made"
        )
        year = self.scraper.get_legislation_year(legislation_url)
        self.assertEqual(year, "2021")

    def test_get_legislation_year_ssi_url(self):
        legislation_url = "https://www.legislation.gov.uk/ssi/2021/370/made"
        year = self.scraper.get_legislation_year(legislation_url)
        self.assertEqual(year, "2021")

    def test_get_legislation_year_invalid_url(self):
        legislation_url = "https://www.invalid-url.com/uksi/2023/1023/made"
        with self.assertRaises(ScraperException):
            self.scraper.get_legislation_year(legislation_url)

    def test_get_legislation_year_no_url(self):
        legislation_url = ""
        with self.assertRaises(ScraperException):
            self.scraper.get_legislation_year(legislation_url)

    def test_get_legislation_year_malformed_url(self):
        legislation_url = "https://www.legislation.gov.uk/uksi/2023"
        with self.assertRaises(ScraperException):
            self.scraper.get_legislation_year(legislation_url)
