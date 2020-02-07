from django.contrib.gis.db import models
from .mixins import DateConstraintMixin, DateDisplayMixin


class OrganisationDivisionSet(DateConstraintMixin, DateDisplayMixin, models.Model):
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

    def __str__(self):
        return "{}:{} ({})".format(self.pk, self.short_title, self.active_period_text)

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


class OrganisationDivision(models.Model):
    """
    Sub parts of an organisation that people can be elected to.

    This could be a ward, constituency or office
    """

    organisation = models.ForeignKey(
        "Organisation", related_name="divisions", on_delete=models.CASCADE
    )
    divisionset = models.ForeignKey(
        "OrganisationDivisionSet",
        related_name="divisions",
        null=False,
        on_delete=models.CASCADE,
    )
    name = models.CharField(blank=True, max_length=255)
    official_identifier = models.CharField(blank=True, max_length=255, db_index=True)
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
        unique_together = ("organisation", "divisionset", "official_identifier")

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
