from datetime import timedelta

from core.mixins import UpdateElectionsTimestampedModel
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.models import Q
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from model_utils import Choices

from .mixins import DateConstraintMixin, DateDisplayMixin


class OrganisationManager(models.QuerySet):
    def get_date_filter(self, date):
        return models.Q(start_date__lte=date) & (
            models.Q(end_date__gte=date) | models.Q(end_date=None)
        )

    def filter_by_date(self, date):
        return self.filter(self.get_date_filter(date))

    def get_by_date(self, organisation_type, official_identifier, date):
        return self.get(
            models.Q(organisation_type=organisation_type)
            & models.Q(official_identifier=official_identifier)
            & self.get_date_filter(date)
        )


class Organisation(UpdateElectionsTimestampedModel, DateDisplayMixin):
    """
    An organisation that can hold an election in the UK
    """

    ORGTYPES = Choices(
        ("combined-authority", "combined-authority"),
        ("sp", "sp"),
        ("gla", "gla"),
        ("local-authority", "local-authority"),
        ("naw", "naw"),
        ("senedd", "senedd"),
        ("nia", "nia"),
        ("parl", "parl"),
        ("police-area", "police-area"),
        ("europarl", "europarl"),
    )

    official_identifier = models.CharField(
        blank=False, max_length=255, db_index=True
    )
    organisation_type = models.CharField(
        blank=False, max_length=255, choices=ORGTYPES, default="local-authority"
    )
    organisation_subtype = models.CharField(blank=True, max_length=255)
    official_name = models.CharField(blank=True, max_length=255)
    common_name = models.CharField(blank=True, max_length=255)
    slug = models.CharField(blank=True, max_length=100)
    territory_code = models.CharField(blank=True, max_length=10)
    election_types = models.ManyToManyField(
        "elections.ElectionType", through="elections.ElectedRole"
    )
    election_name = models.CharField(blank=True, max_length=255)
    start_date = models.DateField(null=False)
    end_date = models.DateField(blank=True, null=True)
    legislation_url = models.CharField(blank=True, max_length=500, null=True)
    ValidationError = ValueError
    objects = OrganisationManager().as_manager()

    def __str__(self):
        return "{} ({})".format(self.name, self.active_period_text)

    @property
    def name(self):
        return (
            self.official_name or self.common_name or self.official_identifier
        )

    class Meta:
        ordering = ("official_name", "-start_date")
        get_latest_by = "start_date"
        unique_together = (
            ("official_identifier", "organisation_type", "start_date"),
            ("official_identifier", "organisation_type", "end_date"),
        )
        """
        Note:
        This model also has an additional constraint to prevent
        overlapping start and end dates which is defined in
        organisations/migrations/0034_end_date_constraint.py
        """

    def get_url(self, view, ext=None):
        args = (
            self.organisation_type,
            self.official_identifier,
            self.start_date,
        )
        args = args + (ext,) if ext else args
        return reverse(view, args=args)

    def get_absolute_url(self):
        return self.get_url("organisation_view")

    def format_geography_link(self):
        if len(self.geographies.all()) == 0:
            return None
        if not self.geographies.latest().gss:
            return None
        return "https://mapit.mysociety.org/area/{}.html".format(
            self.geographies.latest().gss
        )

    def get_geography(self, date):
        if len(self.geographies.all()) == 0:
            return None
        if len(self.geographies.all()) == 1:
            return self.geographies.all()[0]
        if date < self.start_date:
            raise ValueError(
                "date %s is before organisation start_date (%s)"
                % (date.isoformat(), self.start_date.isoformat())
            )
        if self.end_date and date > self.end_date:
            raise ValueError(
                "date %s is after organisation end_date (%s)"
                % (date.isoformat(), self.end_date.isoformat())
            )

        try:
            return self.geographies.get(
                (models.Q(start_date__lte=date) | models.Q(start_date=None))
                & (models.Q(end_date__gte=date) | models.Q(end_date=None))
            )
        except OrganisationGeography.DoesNotExist:
            return None


class OrganisationGeography(
    DateConstraintMixin, DateDisplayMixin, models.Model
):
    organisation = models.ForeignKey(
        "Organisation", related_name="geographies", on_delete=models.CASCADE
    )
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    gss = models.CharField(blank=True, max_length=20)
    legislation_url = models.CharField(blank=True, max_length=500, null=True)
    geography = models.MultiPolygonField(null=True)
    source = models.CharField(blank=True, max_length=255)

    def __str__(self):
        if self.gss:
            return self.gss
        return "{name} ({dates})".format(
            name=self.organisation.name, dates=self.active_period_text
        )

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.check_start_date()
        self.check_end_date()

        super().save(*args, **kwargs)

        self.subdivided.all().delete()
        sql = """
            INSERT INTO organisations_organisationgeographysubdivided (geography, organisation_geography_id)
            SELECT st_subdivide(geography) as geography, id as division_geography_id
            FROM organisations_organisationgeography og
            WHERE og.id=%s;
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, [self.id])

    class Meta:
        verbose_name_plural = "Organisation Geographies"
        ordering = ("-start_date",)
        get_latest_by = "start_date"
        unique_together = (
            ("organisation", "start_date"),
            ("organisation", "end_date"),
        )
        """
        Note:
        This model also has an additional constraint to prevent
        overlapping start and end dates (but allows both to be NULL).
        This is defined in
        organisations/migrations/0040_end_date_constraint.py
        """


class OrganisationGeographySubdivided(models.Model):
    geography = models.PolygonField(db_index=True, spatial_index=True)
    organisation_geography = models.ForeignKey(
        OrganisationGeography,
        on_delete=models.CASCADE,
        related_name="subdivided",
    )

    POPULATE_SQL = """
    TRUNCATE organisations_organisationgeographysubdivided;
    INSERT INTO organisations_organisationgeographysubdivided (geography, organisation_geography_id)
        SELECT st_subdivide(geography) as geography, id as organisation_geography_id 
        FROM organisations_organisationgeography;
    """

    POPULATE_WHERE_MISSING_SQL = """
    WITH missing_subdivided_geography AS (
    SELECT og.id
    FROM organisations_organisationgeography og
        LEFT JOIN organisations_organisationgeographysubdivided ogs
            ON og.id = ogs.organisation_geography_id
    WHERE ogs.id IS NULL
    )
    INSERT INTO organisations_organisationgeographysubdivided (geography, organisation_geography_id)
        SELECT st_subdivide(geography) as geography, id as division_geography_id
        FROM organisations_organisationgeography og
        WHERE og.id IN (SELECT id FROM missing_subdivided_geography);
    """


class OrganisationChangeType(models.TextChoices):
    CREATE = "CREATE", "Create"
    UPDATE = "UPDATE", "Update"
    END = "END", "End"


class OrganisationChange(models.Model):
    organisation_change_legislation = models.ForeignKey(
        "OrganisationChangeLegislation", on_delete=models.CASCADE
    )
    organisation = models.ForeignKey(
        "Organisation",
        on_delete=models.CASCADE,
        limit_choices_to=~Q(organisation_type__in=["police-area", "europarl"]),
    )
    change_type = models.CharField(
        max_length=10, choices=OrganisationChangeType.choices
    )
    information_url = models.URLField(
        blank=True,
        default="",
        help_text=(
            "A link to an org-specific information resource. "
            "This field can be used in addition to, or instead of, "
            "the multi-org information url on the legislation, "
            "if the affected org has its own dedicated info resource."
        ),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organisation_change_legislation", "organisation"],
                name="unique_ocl_organisation",
            )
        ]

    def __str__(self):
        return f"Org Change for {self.organisation.common_name} ({self.change_type})"

    def clean(self):
        super().clean()
        ocl_effective_date = self.organisation_change_legislation.effective_date
        if not ocl_effective_date:
            # If the OCL's effective date is not set, we can skip this validation.
            # This is because we still want to be able to communicate organisation changes to users
            # before we know the effective date of the legislation.
            return

        org_start_date = self.organisation.start_date
        org_end_date = self.organisation.end_date

        error_kwargs = {"message": {}, "code": "invalid_date"}

        if self.change_type == OrganisationChangeType.END and (
            org_end_date is None or org_end_date >= ocl_effective_date
        ):
            error_kwargs["message"]["organisation"] = (
                f"The Organisation's end date ({org_end_date}) must be before the OCL's effective_date {ocl_effective_date}"
            )
            raise ValidationError(**error_kwargs)

        if (
            self.change_type == OrganisationChangeType.CREATE
            and org_start_date < (ocl_effective_date - timedelta(days=365))
        ):
            # New orgs normally have shadow elections the year before they actually are created,
            # so, in order for us to create those elections, we set their start date earlier than the actual effective date
            error_kwargs["message"]["organisation"] = (
                f"The Organisation's start date ({org_start_date}) must be within a year of the OCL's effective_date ({ocl_effective_date})"
            )
            raise ValidationError(**error_kwargs)

        if self.change_type == OrganisationChangeType.UPDATE and (
            ocl_effective_date < org_start_date
            or (org_end_date is not None and ocl_effective_date > org_end_date)
        ):
            error_kwargs["message"]["organisation"] = (
                f"The OCL's effective_date ({ocl_effective_date}) must be between the Organisation's start date ({org_start_date}) and its end date ({org_end_date})"
            )
            raise ValidationError(**error_kwargs)


class OCLPublicVisibility(models.TextChoices):
    HIDDEN = "HIDDEN", "Hidden"
    INFORM = "INFORM", "Inform"
    MAP = "MAP", "Map"


class OrganisationChangeLegislation(TimeStampedModel):
    """
    A model for legislation that can:

    - Create or end organisations
    - Modify organisation boundaries

    Some examples include:

    - The Surrey (Structural Changes) Order 2026: https://www.legislation.gov.uk/uksi/2026/264/made
    - The Glasgow and North Lanarkshire Boundaries Amendment Order 2018: https://www.legislation.gov.uk/ssi/2018/308/made
    - The Hampshire and the Solent Combined County Authority Regulations 2026: https://www.legislation.gov.uk/uksi/2026/595

    """

    provisional_name = models.CharField(blank=True, default="", max_length=255)
    affected_organisations = models.ManyToManyField(
        "Organisation",
        through=OrganisationChange,
        blank=True,
    )
    public_visibility = models.CharField(
        choices=OCLPublicVisibility.choices, default=OCLPublicVisibility.HIDDEN
    )
    information_url = models.URLField(
        blank=True,
        default="",
        help_text="A Link to a general, multi-org information resource",
    )
    explanation = models.TextField(blank=True, default="")
    legislation_title = models.CharField(blank=True, default="")
    legislation_url = models.URLField(blank=True, default="")
    legislation_made = models.BooleanField(default=False)
    effective_date = models.DateField(blank=True, null=True, default=None)

    class Meta(TimeStampedModel.Meta):
        verbose_name_plural = "Organisation Change Legislation"
        constraints = [
            models.CheckConstraint(
                condition=Q(provisional_name__gt="")
                | Q(legislation_title__gt=""),
                name="provisional_name_or_legislation_title_not_blank",
            )
        ]

    def __str__(self):
        return self.generic_title

    @property
    def generic_title(self):
        if self.legislation_title:
            return self.legislation_title
        return self.provisional_name
