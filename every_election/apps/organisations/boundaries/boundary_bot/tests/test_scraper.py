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
        self.scraper.data["allerdale"][
            "latest_event"
        ] = "Making our recommendation into law"
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


class TestGetLegislationYear(TestCase):
    def setUp(self):
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
