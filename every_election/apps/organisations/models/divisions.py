import os
import re

from core.mixins import UpdateElectionsTimestampedModel
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.aggregates import StringAgg
from django.db import connection, transaction
from django.db.models import Q
from django.db.models.fields import BinaryField, CharField
from django.db.models.functions import MD5, Cast, Concat
from django.utils.functional import cached_property
from django_extensions.db.models import TimeStampedModel
from elections.baker import send_event
from organisations.constants import PMTILES_FEATURE_ATTR_FIELDS
from storage.s3wrapper import S3Wrapper

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
    pmtiles_md5_hash = models.CharField(max_length=32, blank=True)
    ValidationError = ValueError

    objects = DivisionSetQuerySet.as_manager()

    def __str__(self):
        return "{}:{} ({})".format(
            self.pk, self.short_title, self.active_period_text
        )

    @cached_property
    def has_pmtiles_file(self):
        try:
            self.pmtiles_file_name
        except ValueError:
            return False

        if settings.PUBLIC_DATA_BUCKET:
            s3_wrapper = S3Wrapper(settings.PUBLIC_DATA_BUCKET)
            if s3_wrapper.check_s3_obj_exists(self.pmtiles_s3_key):
                return True
        else:
            if os.path.exists(
                f"{settings.STATIC_ROOT}/pmtiles-store/{self.pmtiles_file_name}"
            ):
                return True
        return False

    @property
    def pmtiles_file_name(self):
        if not self.pmtiles_md5_hash or not self.organisation.slug:
            raise ValueError("Missing PMTiles MD5 hash or organisation slug.")
        return f"{self.organisation.slug}_{self.id}_{self.pmtiles_md5_hash}.pmtiles"

    @property
    def pmtiles_s3_key(self):
        return f"pmtiles-store/{self.pmtiles_file_name}"

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

    def get_division_geographies(self):
        if self.pk:
            return DivisionGeography.objects.filter(
                division__divisionset=self
            ).order_by("id")
        return DivisionGeography.objects.none()

    def generate_pmtiles_md5_hash(self):
        """Generate an MD5 hash based on the given feature attributes and geographies."""
        div_geogs = self.get_division_geographies()
        aggregate_dict = div_geogs.annotate(
            fields_concat=Concat(
                *PMTILES_FEATURE_ATTR_FIELDS,
                MD5(Cast("geography", output_field=BinaryField())),
                output_field=CharField(),
            )
        ).aggregate(result_hash=MD5(StringAgg("fields_concat", delimiter="")))

        return aggregate_dict["result_hash"]

    def save(self, *args, **kwargs):
        self.check_end_date()

        # generate pmtiles md5 hash if missing
        if (
            self.get_division_geographies().exists()
            and not self.pmtiles_md5_hash
        ):
            self.pmtiles_md5_hash = self.generate_pmtiles_md5_hash()

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


class TerritoryCode(models.TextChoices):
    ENG = ("ENG", "England")
    NIR = ("NIR", "Northern Ireland")
    SCT = ("SCT", "Scotland")
    WLS = ("WLS", "Wales")


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
    territory_code = models.CharField(
        blank=False,
        max_length=10,
        choices=TerritoryCode.choices,
        verbose_name="Territory",
    )
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

        link = f"https://mapit.mysociety.org/area/{code}.html"
        if self.divisionset.end_date:
            link += "?min_generation=1"

        return link


class DivisionGeography(models.Model):
    division = models.OneToOneField(
        OrganisationDivision, related_name="geography", on_delete=models.CASCADE
    )
    geography = models.MultiPolygonField()
    source = models.CharField(blank=True, max_length=255)

    @transaction.atomic
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.subdivided.all().delete()
        sql = """
            INSERT INTO organisations_divisiongeographysubdivided (geography, division_geography_id)
            SELECT st_subdivide(geography) as geography, id as division_geography_id
            FROM organisations_divisiongeography dg
            WHERE dg.id=%s;
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, [self.id])


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

    POPULATE_WHERE_MISSING_SQL = """
    WITH missing_subdivided_geography AS (
    SELECT odg.id
    FROM organisations_divisiongeography odg
        LEFT JOIN organisations_divisiongeographysubdivided odgs
            ON odg.id = odgs.division_geography_id
    WHERE odgs.id IS NULL
    )
    INSERT INTO organisations_divisiongeographysubdivided (geography, division_geography_id)
        SELECT st_subdivide(geography) as geography, id as division_geography_id
        FROM organisations_divisiongeography dg
        WHERE dg.id IN (SELECT id FROM missing_subdivided_geography);
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
        return bool(self.boundaries_url)

    @property
    def can_make_end_date_csv(self):
        return bool(
            self.effective_date and self.organisation and not self.divisionset
        )

    @property
    def can_make_eco_csv(self):
        return bool(
            self.consultation_url
            and self.cleaned_legislation_url
            and self.legislation_title
            and self.organisation
            and not self.divisionset
        )

    @property
    def can_write_csv_to_s3(self):
        return bool(
            self.can_make_eco_csv
            and self.can_make_end_date_csv
            and not self.divisionset
        )

    def save(self, push_event=True, *args, **kwargs):
        super().save(*args, **kwargs)
        if push_event:
            send_event(
                detail={"description": "boundary review saved"},
                detail_type="boundary_change_set_changed",
            )
