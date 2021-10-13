from django.contrib.gis.db import models
from django.urls import reverse

from model_utils import Choices

from core.mixins import UpdateElectionsTimestampedModel
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

    official_identifier = models.CharField(blank=False, max_length=255, db_index=True)
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
        return self.official_name or self.common_name or self.official_identifier

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
        args = (self.organisation_type, self.official_identifier, self.start_date)
        args = args + (ext,) if ext else args
        return reverse(view, args=args)

    def get_absolute_url(self):
        return self.get_url("organisation_view")

    def format_geography_link(self):
        if len(self.geographies.all()) == 0:
            return None
        if not self.geographies.latest().gss:
            return None
        return "https://mapit.mysociety.org/area/{}".format(
            self.geographies.latest().gss
        )

    def get_geography(self, date):
        if len(self.geographies.all()) == 0:
            return None
        elif len(self.geographies.all()) == 1:
            return self.geographies.all()[0]
        else:
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


class OrganisationGeography(DateConstraintMixin, DateDisplayMixin, models.Model):
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

    def save(self, *args, **kwargs):
        self.check_start_date()
        self.check_end_date()
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Organisation Geographies"
        ordering = ("-start_date",)
        get_latest_by = "start_date"
        unique_together = (("organisation", "start_date"), ("organisation", "end_date"))
        """
        Note:
        This model also has an additional constraint to prevent
        overlapping start and end dates (but allows both to be NULL).
        This is defined in
        organisations/migrations/0040_end_date_constraint.py
        """
