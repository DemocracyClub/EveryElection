import datetime as dt

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase
from elections.tests.factories import ElectionFactory
from organisations.models import (
    DivisionGeographySubdivided,
    Organisation,
    OrganisationChangeType,
    OrganisationGeographySubdivided,
)
from organisations.tests.factories import (
    CompletedOrganisationBoundaryReviewFactory,
    DivisionGeographyFactory,
    IncompleteOrganisationBoundaryReviewFactory,
    OrganisationChangeFactory,
    OrganisationChangeLegislationFactory,
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
    OrganisationFactory,
    OrganisationGeographyFactory,
    UnprocessedOrganisationBoundaryReviewFactory,
)


class TestOrganisationManager(TestCase):
    def setUp(self):
        super().setUp()
        OrganisationFactory(
            official_identifier="TEST1",
            official_name="Foo & Bar District Council",
            organisation_type="local-authority",
            start_date=dt.date(2016, 10, 1),
            end_date=dt.date(2017, 10, 1),
        )
        OrganisationFactory(
            official_identifier="TEST1",
            official_name="Bar with Foo District Council",
            organisation_type="local-authority",
            start_date=dt.date(2017, 10, 2),
            end_date=None,
        )

        OrganisationFactory(
            official_identifier="TEST2",
            official_name="Baz District Council",
            organisation_type="local-authority",
            start_date=dt.date(2016, 10, 1),
            end_date=dt.date(2017, 10, 1),
        )
        OrganisationFactory(
            official_identifier="TEST2",
            official_name="Baz Metropolitan Borough Council",
            organisation_type="local-authority",
            start_date=dt.date(2017, 10, 2),
            end_date=dt.date(2018, 10, 2),
        )

    def test_date_before_start(self):
        with self.assertRaises(Organisation.DoesNotExist):
            Organisation.objects.all().get_by_date(
                official_identifier="TEST1",
                organisation_type="local-authority",
                date=dt.date(2015, 12, 1),
            )

    def test_date_after_end(self):
        with self.assertRaises(Organisation.DoesNotExist):
            Organisation.objects.all().get_by_date(
                official_identifier="TEST2",
                organisation_type="local-authority",
                date=dt.date(2019, 12, 1),
            )

    def test_date_valid_in_range(self):
        o = Organisation.objects.all().get_by_date(
            official_identifier="TEST1",
            organisation_type="local-authority",
            date=dt.date(2016, 12, 1),
        )
        self.assertEqual("Foo & Bar District Council", o.official_name)

    def test_date_valid_with_null_end(self):
        o = Organisation.objects.all().get_by_date(
            official_identifier="TEST1",
            organisation_type="local-authority",
            date=dt.date(2018, 12, 1),
        )
        self.assertEqual("Bar with Foo District Council", o.official_name)


class TestOrganisationGeographies(TestCase):
    def test_no_geographies(self):
        org = OrganisationFactory()
        self.assertEqual(None, org.get_geography(dt.date.today()))
        self.assertEqual(None, org.format_geography_link())

    def test_one_geography_with_gss(self):
        org = OrganisationFactory()
        geo = OrganisationGeographyFactory(organisation=org, gss="X01000001")
        self.assertEqual(geo, org.get_geography(dt.date.today()))
        self.assertEqual(
            geo, org.get_geography("doesn't even need to be a date")
        )
        self.assertEqual(
            "https://mapit.mysociety.org/area/X01000001.html",
            org.format_geography_link(),
        )
        geo.gss = ""
        geo.save()
        self.assertEqual(None, org.format_geography_link())

    def test_one_geography_no_gss(self):
        org = OrganisationFactory()
        geo = OrganisationGeographyFactory(organisation=org, gss="")
        self.assertEqual(geo, org.get_geography(dt.date.today()))
        self.assertEqual(None, org.format_geography_link())

    def test_multiple_geographies(self):
        org = OrganisationFactory(start_date=dt.date(2001, 1, 1), end_date=None)
        OrganisationGeographyFactory(
            organisation=org,
            gss="X01000001",
            start_date=None,
            end_date="2001-01-01",
        )
        OrganisationGeographyFactory(
            organisation=org,
            gss="X01000002",
            start_date="2001-01-02",
            end_date="2002-01-01",
        )
        OrganisationGeographyFactory(
            organisation=org,
            gss="X01000003",
            start_date="2002-01-02",
            end_date=None,
        )
        self.assertEqual(
            "X01000001", org.get_geography(dt.date(2001, 1, 1)).gss
        )
        self.assertEqual(
            "X01000002", org.get_geography(dt.date(2001, 7, 20)).gss
        )
        self.assertEqual(
            "X01000003", org.get_geography(dt.date(2099, 1, 1)).gss
        )
        with self.assertRaises(ValueError):
            org.get_geography(dt.date(1900, 1, 1))  # before the org start date

    def test_create_subdivided(self):
        # no subdivided geographies exist before we start
        self.assertEqual(
            OrganisationGeographySubdivided.objects.all().count(), 0
        )

        org = OrganisationFactory()
        geo = OrganisationGeographyFactory(organisation=org, gss="")

        # creating an OrganisationGeography object should create one or more
        # related OrganisationGeographySubdivided objects
        self.assertTrue(
            OrganisationGeographySubdivided.objects.filter(
                organisation_geography=geo
            ).count()
            >= 1
        )

    def test_update_subdivided(self):
        org = OrganisationFactory()
        geo = OrganisationGeographyFactory(organisation=org, gss="")

        orig_id = geo.subdivided.all()[0].id
        geo.save()

        # We should have deleted and re-created the related
        # OrganisationGeographySubdivided objects
        self.assertNotEqual(orig_id, geo.subdivided.all()[0].id)


class TestOrganisationDivision(TestCase):
    def test_format_geography_invalid(self):
        self.assertIsNone(
            OrganisationDivisionFactory(
                official_identifier="foo"
            ).format_geography_link()
        )

    def test_format_geography_empty(self):
        self.assertIsNone(
            OrganisationDivisionFactory(
                official_identifier=""
            ).format_geography_link()
        )

    def test_format_geography_not_gss(self):
        self.assertIsNone(
            OrganisationDivisionFactory(
                official_identifier="foo:X01000001"
            ).format_geography_link()
        )

    def test_format_geography_valid(self):
        self.assertEqual(
            "https://mapit.mysociety.org/area/X01000001.html?min_generation=1",
            OrganisationDivisionFactory(
                official_identifier="gss:X01000001"
            ).format_geography_link(),
        )

    def test_save_calls_update(self):
        self.division = OrganisationDivisionFactory()
        ElectionFactory.create_batch(size=10, division=self.division)
        self.assertNotIn(
            self.division.modified,
            self.division.election_set.values_list("modified", flat=True),
        )
        self.division.save()
        modified_dates = (
            self.division.election_set.values_list("modified", flat=True)
            .order_by()
            .distinct()
        )
        self.assertEqual([self.division.modified], list(modified_dates))


class TestOrganisationDivisionGeography(TestCase):
    def test_create_subdivided(self):
        # no subdivided geographies exist before we start
        self.assertEqual(DivisionGeographySubdivided.objects.all().count(), 0)

        div = OrganisationDivisionFactory()
        geo = DivisionGeographyFactory(division=div)

        # creating an DivisionGeography object should create one or more
        # related DivisionGeographySubdivided objects
        self.assertTrue(
            DivisionGeographySubdivided.objects.filter(
                division_geography=geo
            ).count()
            >= 1
        )

    def test_update_subdivided(self):
        div = OrganisationDivisionFactory()
        geo = DivisionGeographyFactory(division=div)

        orig_id = geo.subdivided.all()[0].id
        geo.save()

        # We should have deleted and re-created the related
        # DivisionGeographySubdivided objects
        self.assertNotEqual(orig_id, geo.subdivided.all()[0].id)


class TestDateConstraints(TestCase):
    def setUp(self):
        super().setUp()
        self.org = OrganisationFactory(
            start_date=dt.date(2001, 1, 1), end_date=dt.date(2002, 1, 1)
        )

    def test_save_divisionset_before_start(self):
        """
        This seems strange on the face of it, but it does legitimately happen.

        For example, the Local Government Act 1972 reformed local
        government in England and Wales on 1 April 1974
        but Elections were held to the new authorities in 1973,
        and they acted as "shadow authorities" until the handover date.

        Similarly, when Northern Ireland was re-organised from 26
        local authorities into 11, they held elections using the new
        electoral divisions in 2014 even though the new local authorities
        weren't officially created until April 2015.
        """
        try:
            OrganisationDivisionSetFactory(
                organisation=self.org,
                start_date=dt.date(2000, 1, 1),
                end_date=None,
            )
        except ValidationError:
            self.fail("ValidationError raised unexpectedly!")

    def test_save_divisionset_after_end(self):
        with self.assertRaises(ValidationError):
            OrganisationDivisionSetFactory(
                organisation=self.org,
                start_date=dt.date(2001, 1, 1),
                end_date=dt.date(2003, 1, 1),
            )

    def test_save_divisionset_valid(self):
        try:
            OrganisationDivisionSetFactory(
                organisation=self.org,
                start_date=dt.date(2001, 1, 1),
                end_date=dt.date(2002, 1, 1),
            )
        except ValidationError:
            self.fail("ValidationError raised unexpectedly!")

    def test_save_organisationgeography_before_start(self):
        with self.assertRaises(ValidationError):
            OrganisationGeographyFactory(
                organisation=self.org,
                start_date=dt.date(2000, 1, 1),
                end_date=None,
            )

    def test_save_organisationgeography_after_end(self):
        with self.assertRaises(ValidationError):
            OrganisationGeographyFactory(
                organisation=self.org,
                start_date=dt.date(2001, 1, 1),
                end_date=dt.date(2003, 1, 1),
            )

    def test_save_organisationgeography_valid(self):
        try:
            OrganisationGeographyFactory(
                organisation=self.org,
                start_date=dt.date(2001, 1, 1),
                end_date=dt.date(2002, 1, 1),
            )
        except ValidationError:
            self.fail("ValidationError raised unexpectedly!")


class TestOrganisation(TestCase):
    def setUp(self):
        self.org = OrganisationFactory()
        ElectionFactory.create_batch(size=10, organisation=self.org)

    def test_save_calls_update(self):
        self.assertNotIn(
            self.org.modified,
            self.org.election_set.values_list("modified", flat=True),
        )
        self.org.save()
        modified_dates = (
            self.org.election_set.values_list("modified", flat=True)
            .order_by()
            .distinct()
        )
        self.assertEqual([self.org.modified], list(modified_dates))


class TestOrganisationDivisionBoundaryReview(TestCase):
    def setUp(self):
        self.unprocessed_review = UnprocessedOrganisationBoundaryReviewFactory()
        self.processed_review = CompletedOrganisationBoundaryReviewFactory(
            boundaries_url="path/to/processed_review_polys.zip"
        )
        self.incomplete_review = IncompleteOrganisationBoundaryReviewFactory(
            boundaries_url=""
        )

    def test_boundary_file_name(self):
        self.assertEqual(
            "processed_review_polys.zip",
            self.processed_review.boundary_file_name,
        )
        self.assertEqual("", self.incomplete_review.boundary_file_name)
        self.assertEqual(
            "polygons.zip", self.unprocessed_review.boundary_file_name
        )

    def test_s3_boundaries_key(self):
        self.assertEqual(
            f"{self.processed_review.slug}/The {self.processed_review.organisation.common_name} (Electoral Changes) "
            f"Order 2023/processed_review_polys.zip",
            self.processed_review.s3_boundaries_key,
        )
        self.assertIsNone(self.incomplete_review.s3_boundaries_key)
        self.assertEqual(
            f"{self.unprocessed_review.slug}/The {self.unprocessed_review.organisation.common_name} (Electoral Changes) "
            f"Order 2023/polygons.zip",
            self.unprocessed_review.s3_boundaries_key,
        )

    def test_cleaned_legislation_url(self):
        cases = [
            (
                "http://www.legislation.gov.uk/uksi/2017/1315/contents/made",
                "https://www.legislation.gov.uk/uksi/2017/1315",
            ),
            (
                "https://www.legislation.gov.uk/uksi/2021/1053/contents/made",
                "https://www.legislation.gov.uk/uksi/2021/1053",
            ),
            (
                "https://www.legislation.gov.uk/uksi/2021/417/made",
                "https://www.legislation.gov.uk/uksi/2021/417",
            ),
            (
                "https://www.legislation.gov.uk/uksi/2021/1230/introduction/made",
                "https://www.legislation.gov.uk/uksi/2021/1230",
            ),
        ]
        for raw_url, clean_url in cases:
            obr = CompletedOrganisationBoundaryReviewFactory(
                legislation_url=raw_url
            )
            self.assertEqual(
                clean_url,
                obr.cleaned_legislation_url,
            )

    def test_generic_title(self):
        self.assertEqual(
            f"Boundary review for {self.incomplete_review.organisation.common_name} ({self.incomplete_review.status})",
            self.incomplete_review.generic_title,
        )
        self.assertEqual(
            self.unprocessed_review.legislation_title,
            self.unprocessed_review.generic_title,
        )
        self.assertEqual(
            self.processed_review.legislation_title,
            self.processed_review.generic_title,
        )


class TestOrganisationChangeLegislation(TestCase):
    def test_constraint_provisional_name_or_legislation_title_blank(self):
        OrganisationChangeLegislationFactory(
            provisional_name="test name",
            legislation_title="test title",
        )
        OrganisationChangeLegislationFactory(
            provisional_name="",
            legislation_title="test title",
        )
        OrganisationChangeLegislationFactory(
            provisional_name="test name",
            legislation_title="",
        )
        with self.assertRaises(IntegrityError):
            OrganisationChangeLegislationFactory(
                provisional_name="", legislation_title=""
            )


class TestOrgChange(TestCase):
    def setUp(self):
        self.date = dt.date(2026, 4, 1)
        self.day_before = self.date - dt.timedelta(days=1)
        self.day_after = self.date + dt.timedelta(days=1)

    def test_ending_org_end_date_before_effective_date_is_valid(self):
        org_change = OrganisationChangeFactory(
            organisation_change_legislation__effective_date=self.date,
            organisation__end_date=self.day_before,
            change_type=OrganisationChangeType.END,
        )
        org_change.clean()

    def test_ending_org_end_date_after_effective_date_is_invalid(self):
        org_change = OrganisationChangeFactory(
            organisation_change_legislation__effective_date=self.date,
            organisation__end_date=self.day_after,
            change_type=OrganisationChangeType.END,
        )
        with self.assertRaises(ValidationError) as e:
            org_change.clean()
        self.assertIn("must be before", str(e.exception))

    def test_created_org_start_date_after_effective_date_is_valid(self):
        org_change = OrganisationChangeFactory(
            organisation_change_legislation__effective_date=self.date,
            organisation__start_date=self.day_after,
            change_type=OrganisationChangeType.CREATE,
        )
        org_change.clean()

    def test_created_org_start_date_within_one_year_of_effective_date_is_valid(
        self,
    ):
        org_change = OrganisationChangeFactory(
            organisation_change_legislation__effective_date=self.date,
            organisation__start_date=(self.date - dt.timedelta(days=364)),
            change_type=OrganisationChangeType.CREATE,
        )
        org_change.clean()

    def test_created_org_start_date_over_one_year_of_effective_date_is_invalid(
        self,
    ):
        org_change = OrganisationChangeFactory(
            organisation_change_legislation__effective_date=self.date,
            organisation__start_date=(self.date - dt.timedelta(days=366)),
            change_type=OrganisationChangeType.CREATE,
        )
        with self.assertRaises(ValidationError) as e:
            org_change.clean()
        self.assertIn("must be within", str(e.exception))

    def test_effective_date_within_updated_org_dates_is_valid(self):
        org_change = OrganisationChangeFactory(
            organisation_change_legislation__effective_date=self.date,
            organisation__start_date=self.day_before,
            organisation__end_date=self.day_after,
            change_type=OrganisationChangeType.UPDATE,
        )
        org_change.clean()

    def test_effective_date_outside_updated_org_dates_is_invalid(self):
        org_change = OrganisationChangeFactory(
            organisation_change_legislation__effective_date=(
                self.date - dt.timedelta(days=2)
            ),
            organisation__start_date=self.day_before,
            organisation__end_date=self.day_after,
            change_type=OrganisationChangeType.UPDATE,
        )
        with self.assertRaises(ValidationError) as e:
            org_change.clean()
        self.assertIn("must be between", str(e.exception))

    def test_no_validation_if_no_effective_date(self):
        org_change = OrganisationChangeFactory(
            organisation__end_date=self.day_after,
            change_type=OrganisationChangeType.END,
        )
        org_change.clean()  # does not raise when effective date is not set
        org_change.organisation_change_legislation.effective_date = self.date
        with self.assertRaises(ValidationError):
            org_change.clean()  # raises with effective date set
