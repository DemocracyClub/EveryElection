from django.test import TestCase
from organisations.tests.factories import (
    CompletedOrganisationBoundaryReviewFactory,
    DivisionGeographyFactory,
    IncompleteOrganisationBoundaryReviewFactory,
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
    OrganisationFactory,
    UnprocessedOrganisationBoundaryReviewFactory,
)


class TestElectionIDs(TestCase):
    def test_organisation_factory(self):
        o = OrganisationFactory()
        assert o.slug == "org-{}".format(o.official_identifier)

    def test_organisation_division_set_factory(self):
        ods = OrganisationDivisionSetFactory()
        assert ods.organisation.slug.startswith("org-")

    def test_organisation_division_factory(self):
        od = OrganisationDivisionFactory()
        assert od.organisation.slug.startswith("org-")

    def test_division_geography_factory(self):
        DivisionGeographyFactory()

    def test_completed_organisation_boundary_review_factory(self):
        completed_review = CompletedOrganisationBoundaryReviewFactory()
        self.assertTrue(completed_review.slug.startswith("org-"))
        self.assertTrue(completed_review.consultation_url)
        self.assertTrue(completed_review.legislation_made)
        self.assertTrue(completed_review.legislation_url)
        self.assertEqual(
            f"The {completed_review.organisation.common_name} (Electoral Changes) Order 2023",
            completed_review.legislation_title,
        )
        self.assertEqual(
            completed_review.effective_date,
            completed_review.divisionset.start_date,
        )
        self.assertIsNotNone(completed_review.effective_date)

    def test_incomplete_organisation_boundary_review_factory(self):
        IncompleteOrganisationBoundaryReviewFactory()
        incomplete_review = IncompleteOrganisationBoundaryReviewFactory()
        self.assertIsNone(incomplete_review.divisionset)
        self.assertTrue(incomplete_review.slug.startswith("org-"))
        self.assertTrue(incomplete_review.consultation_url)
        self.assertIsNone(incomplete_review.legislation_title)
        self.assertIsNone(incomplete_review.legislation_url)
        self.assertFalse(incomplete_review.legislation_made)
        self.assertIsNone(incomplete_review.effective_date)

    def test_unprocessed_organisation_boundary_review_factory(self):
        unprocessed_review = UnprocessedOrganisationBoundaryReviewFactory()
        self.assertIsNone(unprocessed_review.divisionset)
        self.assertTrue(unprocessed_review.slug.startswith("org-"))
        self.assertTrue(unprocessed_review.consultation_url)
        self.assertTrue(unprocessed_review.legislation_made)
        self.assertTrue(unprocessed_review.legislation_url)
        self.assertIn(
            "(Electoral Changes)", unprocessed_review.legislation_title
        )
        self.assertEqual(unprocessed_review.effective_date, "2024-05-02")
