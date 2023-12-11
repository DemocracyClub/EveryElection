import re

from core.mixins import UpdateElectionsTimestampedModel
from django.contrib.gis.db import models
from django.db.models import Q
from django_extensions.db.models import TimeStampedModel

from .mixins import DateConstraintMixin, DateDisplayMixin


class DivisionSetQuerySet(models.QuerySet):
    def filter_by_date(self, date):
        return self.filter(
            models.Q(start_date__lte=date)
            & (models.Q(end_date__gte=date) | models.Q(end_date=None))
        )


class OrganisationDivisionSet(
    DateConstraintMixin, DateDisplayMixin, models.Model
):
    organisation = models.ForeignKey(
        "Organisation", related_name="divisionset", on_delete=models.CASCADE
    )
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=True, blank=True)
    legislation_url = models.CharField(blank=True, max_length=500, null=True)
    consultation_url = models.CharField(blank=True, max_length=500, null=True)
    short_title = models.CharField(blank=True, max_length=200)
    notes = models.TextField(blank=True)
    ValidationError = ValueError

    objects = DivisionSetQuerySet.as_manager()

    def __str__(self):
        return "{}:{} ({})".format(
            self.pk, self.short_title, self.active_period_text
        )

    @property
    def has_related_geographies(self):
        found_geography = False
        for d in self.divisions.all():
            try:
                d.geography
                found_geography = True
                break
            except DivisionGeography.DoesNotExist:
                pass
        return found_geography

    def divisions_by_type(self):
        divisions_by_type = {}
        divisions = self.divisions.all()
        for division in divisions:
            if division.division_type not in divisions_by_type:
                divisions_by_type[division.division_type] = [division]
            else:
                divisions_by_type[division.division_type].append(division)
        return divisions_by_type

    def save(self, *args, **kwargs):
        self.check_end_date()
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Organisation Division Sets"
        ordering = ("-start_date",)
        get_latest_by = "start_date"
        unique_together = ("organisation", "start_date")
        unique_together = ("organisation", "end_date")
        """
        Note:
        This model also has an additional constraint to prevent
        overlapping start and end dates which is defined in
        organisations/migrations/0031_end_date_constraint.py
        """


class DivisionManager(models.QuerySet):
    def filter_by_date(self, date):
        return self.filter(
            models.Q(divisionset__start_date__lte=date)
            & (
                models.Q(divisionset__end_date__gte=date)
                | models.Q(divisionset__end_date=None)
            )
        )

    def filter_with_temp_id(self):
        return self.extra(
            where=[
                "LEFT(organisations_organisationdivision.official_identifier,4) != 'gss:'",
                "LEFT(organisations_organisationdivision.official_identifier,8) != 'unit_id:'",
                "LEFT(organisations_organisationdivision.official_identifier,9) != 'osni_oid:'",
            ]
        )


class OrganisationDivision(UpdateElectionsTimestampedModel):
    """
    Sub parts of an organisation that people can be elected to.

    This could be a ward, constituency or office
    """

    divisionset = models.ForeignKey(
        "OrganisationDivisionSet",
        related_name="divisions",
        null=False,
        on_delete=models.CASCADE,
    )
    name = models.CharField(blank=True, max_length=255)
    official_identifier = models.CharField(
        blank=True, max_length=255, db_index=True
    )
    temp_id = models.CharField(blank=True, max_length=255, db_index=True)
    slug = models.CharField(blank=True, max_length=100)
    division_type = models.CharField(blank=True, max_length=255)
    division_subtype = models.CharField(blank=True, max_length=255)
    division_election_sub_type = models.CharField(blank=True, max_length=2)
    seats_total = models.IntegerField(blank=True, null=True)
    territory_code = models.CharField(blank=True, max_length=10)
    ValidationError = ValueError
    objects = DivisionManager().as_manager()

    def __str__(self):
        return "{}".format(self.name)

    class Meta:
        verbose_name_plural = "Organisation Divisions"
        ordering = ("name",)
        unique_together = ("divisionset", "official_identifier")

    @property
    def organisation(self):
        return self.divisionset.organisation

    @property
    def organisation_id(self):
        return self.organisation.id

    def format_geography_link(self):
        try:
            code_type, code = self.official_identifier.split(":")
        except (ValueError, AttributeError):
            return None

        if code_type.lower() != "gss":
            return None

        return "https://mapit.mysociety.org/area/{}".format(code)


class DivisionGeography(models.Model):
    division = models.OneToOneField(
        OrganisationDivision, related_name="geography", on_delete=models.CASCADE
    )
    geography = models.MultiPolygonField()
    source = models.CharField(blank=True, max_length=255)


class DivisionGeographySubdivided(models.Model):
    geography = models.PolygonField(db_index=True, spatial_index=True)
    division_geography = models.ForeignKey(
        DivisionGeography,
        on_delete=models.CASCADE,
        related_name="subdivided",
    )

    POPULATE_SQL = """
    TRUNCATE organisations_divisiongeographysubdivided;
    INSERT INTO organisations_divisiongeographysubdivided (geography, division_geography_id)
        SELECT st_subdivide(geography) as geography, id as division_geography_id 
        FROM organisations_divisiongeography;
    """


class OrganisationBoundaryReviewQuerySet(models.QuerySet):
    def unprocessed(self):
        """
        Indicates that the OrganisationBoundaryReview has not been processed yet
        """
        return self.exclude(
            Q(organisation__isnull=True)
            | Q(boundaries_url__exact="")
            | Q(legislation_url__exact="")
            | Q(consultation_url__exact="")
            | Q(legislation_title__exact="")
        ).filter(divisionset=None)

    def needs_end_date(self):
        """
        Filters where status is complete, but we need to enter an end date before it's ready for processing
        """
        return self.unprocessed().filter(effective_date=None)


class ReviewStatus(models.TextChoices):
    COMPLETED = "COMPLETED", "Completed"
    CURRENT = "CURRENT", "Currently in Review"


class EditStatus(models.TextChoices):
    UNLOCKED = "UNLOCKED", "Unlocked"
    LOCKED = "LOCKED", "Locked"


class OrganisationBoundaryReview(TimeStampedModel):
    organisation = models.ForeignKey(
        "Organisation", null=True, blank=True, on_delete=models.CASCADE
    )
    divisionset = models.OneToOneField(
        OrganisationDivisionSet, null=True, blank=True, on_delete=models.CASCADE
    )
    legislation_title = models.CharField(blank=True, default="")
    slug = models.CharField()
    consultation_url = models.URLField(blank=True, default="")
    boundaries_url = models.CharField(blank=True, default="")
    status = models.CharField(choices=ReviewStatus.choices)
    latest_event = models.CharField(blank=True, default="")
    legislation_url = models.URLField(blank=True, default="")
    legislation_made = models.BooleanField(default=False)
    effective_date = models.DateField(blank=True, null=True, default=None)
    edit_status = models.CharField(
        choices=EditStatus.choices, default=EditStatus.UNLOCKED
    )

    objects = OrganisationBoundaryReviewQuerySet.as_manager()

    def __str__(self):
        return f"{self.lgbce_review_title}"

    @property
    def lgbce_review_title(self):
        return (
            f"LGBCE review for {self.organisation.common_name} ({self.status})"
        )

    @property
    def s3_directory_key(self):
        if self.legislation_title:
            return f"{self.slug}/{self.legislation_title}"
        return None

    @property
    def s3_boundaries_key(self):
        if (file_name := self.boundary_file_name) and self.s3_directory_key:
            return f"{self.s3_directory_key}/{file_name}"
        return None

    @property
    def s3_eco_key(self):
        return f"{self.s3_directory_key}/eco.csv"

    @property
    def s3_end_date_key(self):
        return f"{self.s3_directory_key}/end_date.csv"

    @property
    def boundary_file_name(self):
        try:
            return self.boundaries_url.split("/")[-1]
        except AttributeError:
            return None

    @property
    def lgbce_boundary_url(self):
        return f"https://www.lgbce.org.uk{self.boundaries_url}"

    @property
    def cleaned_legislation_url(self):
        url = self.legislation_url.replace("/id/", "/")
        url = re.search(
            r"www.legislation.gov.uk/(wsi|uksi|ssi)/\d+/\d+",
            url,
        ).group()
        return f"https://{url}"

    @property
    def generic_title(self):
        if self.legislation_title:
            return self.legislation_title
        return f"Boundary review for {self.organisation.common_name} ({self.status})"

    @property
    def can_upload_boundaries(self):
        if self.boundaries_url:
            return True
        return False

    @property
    def can_make_end_date_csv(self):
        if self.effective_date and self.organisation and not self.divisionset:
            return True
        return False

    @property
    def can_make_eco_csv(self):
        if (
            self.consultation_url
            and self.cleaned_legislation_url
            and self.legislation_title
            and self.organisation
            and not self.divisionset
        ):
            return True
        return False

    @property
    def can_write_csv_to_s3(self):
        if (
            self.can_make_eco_csv
            and self.can_make_end_date_csv
            and self.can_upload_boundaries
            and not self.divisionset
        ):
            return True
        return False
