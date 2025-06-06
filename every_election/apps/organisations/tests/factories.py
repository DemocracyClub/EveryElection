from datetime import date

import factory
from organisations.models import (
    DivisionGeography,
    DivisionGeographySubdivided,
    Organisation,
    OrganisationBoundaryReview,
    OrganisationDivision,
    OrganisationDivisionSet,
    OrganisationGeography,
    OrganisationGeographySubdivided,
    TerritoryCode,
)
from organisations.models.divisions import ReviewStatus


class OrganisationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organisation

    official_identifier = factory.Sequence(lambda n: n)
    organisation_type = "local-authority"
    official_name = factory.Sequence(
        lambda n: "The Organisation %d Council" % n
    )
    common_name = factory.Sequence(lambda n: "Organisation %d" % n)
    slug = factory.Sequence(lambda n: "org-%d" % n)
    territory_code = "ENG"
    # election_types
    # election_name
    start_date = date(2016, 10, 1)


class OrganisationDivisionSetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganisationDivisionSet

    organisation = factory.SubFactory(OrganisationFactory)
    start_date = "2017-05-04"
    end_date = "2055-05-03"
    legislation_url = "https://example.com/the-law"
    consultation_url = "https://example.com/consultation"
    short_title = "Made up boundary changes"
    notes = "This is just for testing."

    @factory.post_generation
    def fetch_from_db(self, *args, **kwargs):
        self.refresh_from_db()


class OrganisationDivisionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganisationDivision

    divisionset = factory.SubFactory(OrganisationDivisionSetFactory)
    name = factory.Sequence(lambda n: "Division %d" % n)
    official_identifier = factory.Sequence(lambda n: n)
    slug = factory.Sequence(lambda n: "%d" % n)
    division_type = "test"
    seats_total = 1
    territory_code = TerritoryCode.ENG


class SubdividedDivisionGeographyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DivisionGeographySubdivided


class SubdividedOrganisationGeographyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganisationGeographySubdivided


class DivisionGeographyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DivisionGeography

    division = factory.SubFactory(OrganisationDivisionFactory)
    geography = "MULTIPOLYGON (((-0.142322981070547 51.5068483965321, -0.142175355949697 51.5066383732171, -0.141985552222889 51.5067171320737, -0.141458319648422 51.5061920704584, -0.141458319648422 51.506034550794, -0.140256229378637 51.5048662629532, -0.140720194044168 51.5046824846112, -0.138674531655237 51.5024770866938, -0.130787132341213 51.5057720168099, -0.12956395276845 51.5051025483037, -0.129142166708876 51.5038029637132, -0.129142166708876 51.5034485251196, -0.129669399283343 51.5028577880039, -0.129943560222066 51.5014531156649, -0.141205248012678 51.5002584537182, -0.142850213645014 51.4995889042081, -0.143145463886716 51.4993394616797, -0.143757053673097 51.498367935661, -0.144115571823735 51.4982235178632, -0.145043501154796 51.4983416779137, -0.146941538422877 51.498367935661, -0.147363324482451 51.4989062161487, -0.147974914268832 51.4995889042081, -0.148987200811808 51.5003897367824, -0.149640969204147 51.500849224529, -0.150737612959038 51.5014793716197, -0.151138309715633 51.5017813140128, -0.150948505988825 51.5018994648395, -0.149872951536913 51.5023195541869, -0.149619879901169 51.5025952357166, -0.149640969204147 51.5030153186501, -0.149408986871382 51.5031334662775, -0.147510949603301 51.5040655090422, -0.147004806331813 51.5044724513128, -0.145844894667986 51.505063167497, -0.144537357883308 51.505785143545, -0.142322981070547 51.5068483965321)))"  # noqa

    @factory.post_generation
    def subdivide(self: DivisionGeography, create, extracted, **kwargs):
        """
        Create fake "subdivided" geographies for testing.

        This will be the actual geography, apart from the fact that the subdivided geography column
        is a Polygon and the  DivisionGeography geography column is a multipolygon.

        To get around this, we can loop over each polygon in the multipolygon to create a model for each

        """
        for geom in self.geography:
            SubdividedDivisionGeographyFactory(
                division_geography=self, geography=geom
            )


class OrganisationGeographyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganisationGeography

    organisation = factory.SubFactory(OrganisationFactory)
    start_date = None
    end_date = None
    gss = factory.Sequence(lambda n: "E00000%d" % n)
    legislation_url = "https://example.com/the-law"
    geography = "MULTIPOLYGON (((-0.16211289446232513 51.51267297506594,-0.10374802629826263 51.51267297506594,-0.10374802629826263 51.47858081771695,-0.16211289446232513 51.47858081771695,-0.16211289446232513 51.51267297506594)))"  # noqa

    @factory.post_generation
    def subdivide(self: OrganisationGeography, create, extracted, **kwargs):
        """
        Create fake "subdivided" geographies for testing.

        This will be the actual geography, apart from the fact that the subdivided geography column
        is a Polygon and the  OrganisationGeography geography column is a multipolygon.

        To get around this, we can loop over each polygon in the multipolygon to create a model for each

        """
        if not self.geography:
            return
        for geom in self.geography:
            SubdividedOrganisationGeographyFactory(
                organisation_geography=self, geography=geom
            )
            SubdividedOrganisationGeographyFactory(
                organisation_geography=self, geography=geom
            )


class IncompleteOrganisationBoundaryReviewFactory(
    factory.django.DjangoModelFactory
):
    class Meta:
        model = OrganisationBoundaryReview

    organisation = factory.SubFactory(OrganisationFactory)
    divisionset = None
    boundaries_url = "/sites/default/files/2023-03/polygons.zip"
    status = ReviewStatus.CURRENT
    latest_event = "Consultation on proposals"
    legislation_made = False
    legislation_url = ""
    legislation_title = ""

    @factory.lazy_attribute
    def slug(self: OrganisationBoundaryReview):
        return self.organisation.slug

    @factory.lazy_attribute
    def consultation_url(self: OrganisationBoundaryReview):
        return f"http://www.lgbce.org.uk/all-reviews/{self.slug}"


class CompletedOrganisationBoundaryReviewFactory(
    factory.django.DjangoModelFactory
):
    class Meta:
        model = OrganisationBoundaryReview

    organisation = factory.SubFactory(OrganisationFactory)
    divisionset = factory.SubFactory(OrganisationDivisionSetFactory)
    boundaries_url = "/sites/default/files/2023-03/polygons.zip"
    status = ReviewStatus.COMPLETED
    latest_event = "Making our recommendation into law"
    legislation_url = "https://www.legislation.gov.uk/uksi/2023/1023/made"
    legislation_made = True

    @factory.lazy_attribute
    def slug(self: OrganisationBoundaryReview):
        return self.organisation.slug

    @factory.lazy_attribute
    def consultation_url(self: OrganisationBoundaryReview):
        return f"http://www.lgbce.org.uk/all-reviews/{self.slug}"

    @factory.lazy_attribute
    def legislation_title(self: OrganisationBoundaryReview):
        return f"The {self.organisation.common_name} (Electoral Changes) Order 2023"

    @factory.lazy_attribute
    def effective_date(self: OrganisationBoundaryReview):
        return self.divisionset.start_date


class UnprocessedOrganisationBoundaryReviewFactory(
    factory.django.DjangoModelFactory
):
    """
    NB divisionset is none
    """

    class Meta:
        model = OrganisationBoundaryReview

    organisation = factory.SubFactory(OrganisationFactory)
    divisionset = None
    boundaries_url = "/sites/default/files/2023-03/polygons.zip"
    status = ReviewStatus.COMPLETED
    latest_event = "Making our recommendation into law"
    legislation_url = "https://www.legislation.gov.uk/uksi/2023/1023/made"
    legislation_made = True
    effective_date = "2024-05-02"

    @factory.lazy_attribute
    def slug(self: OrganisationBoundaryReview):
        return self.organisation.slug

    @factory.lazy_attribute
    def consultation_url(self: OrganisationBoundaryReview):
        return f"http://www.lgbce.org.uk/all-reviews/{self.slug}"

    @factory.lazy_attribute
    def legislation_title(self: OrganisationBoundaryReview):
        return f"The {self.organisation.common_name} (Electoral Changes) Order 2023"
