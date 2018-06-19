from django.core.exceptions import ValidationError
from django.contrib.gis.db import models
from django.urls import reverse
from django.utils.dateparse import parse_date


class DateConstraintMixin:

    def save(self, *args, **kwargs):

        if type(self.start_date) == str:
            self.start_date = parse_date(self.start_date)
        if type(self.end_date) == str:
            self.end_date = parse_date(self.end_date)

        if self.start_date and self.organisation.start_date and self.start_date < self.organisation.start_date:
            raise ValidationError(
                'start_date (%s) must be on or after parent organisation start_date (%s)' %\
                (self.start_date.isoformat(), self.organisation.start_date.isoformat())
            )
        if self.end_date and self.organisation.end_date and self.end_date > self.organisation.end_date:
            raise ValidationError(
                'end_date (%s) must be on or before parent organisation end_date (%s)' %\
                (self.end_date.isoformat(), self.organisation.end_date.isoformat())
            )

        return super().save(*args, **kwargs)


class OrganisationManager(models.QuerySet):

    def filter_by_date(self, date):
        return self.filter(
            start_date__lte=date
        ).filter(
            models.Q(end_date__gte=date) | models.Q(end_date=None)
        )

    def get_by_date(self, organisation_type, official_identifier, date):
        orgs = self.filter(
            organisation_type=organisation_type
        ).filter(
            official_identifier=official_identifier
        ).filter_by_date(date)

        if len(orgs) != 1:
            raise Organisation.DoesNotExist('Organisation matching query does not exist.')
        org = orgs[0]
        return org


class Organisation(models.Model):
    """
    An organisation that can hold an election in the UK
    """
    official_identifier = models.CharField(
        blank=True, max_length=255, db_index=True)
    organisation_type = models.CharField(blank=True, max_length=255)
    organisation_subtype = models.CharField(blank=True, max_length=255)
    official_name = models.CharField(blank=True, max_length=255)
    common_name = models.CharField(blank=True, max_length=255)
    slug = models.CharField(blank=True, max_length=100)
    territory_code = models.CharField(blank=True, max_length=10)
    election_types = models.ManyToManyField(
        'elections.ElectionType', through='elections.ElectedRole')
    election_name = models.CharField(blank=True, max_length=255)
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=True)
    ValidationError = ValueError
    objects = OrganisationManager().as_manager()

    def __str__(self):
        return "{}".format(self.name)

    @property
    def name(self):
        return self.official_name or self.common_name or self.official_identifier

    class Meta:
        ordering = ('official_name', '-start_date')
        get_latest_by = 'start_date'
        unique_together = (
            ('official_identifier', 'organisation_type', 'start_date'),
            ('official_identifier', 'organisation_type', 'end_date')
        )
        """
        Note:
        This model also has an additional constraint to prevent
        overlapping start and end dates which is defined in
        organisations/migrations/0034_end_date_constraint.py
        """

    def get_absolute_url(self):
        return reverse("organisation_view",
            args=(self.organisation_type, self.official_identifier, self.start_date)
        )

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
                    'date %s is before organisation start_date (%s)' %\
                    (date.isoformat(), self.start_date.isoformat())
                )
            if self.end_date and date > self.end_date:
                raise ValueError(
                    'date %s is after organisation end_date (%s)' %\
                    (date.isoformat(), self.end_date.isoformat())
                )
            geogs = self.geographies.filter(
                models.Q(start_date__lte=date) | models.Q(start_date=None)
            ).filter(
                models.Q(end_date__gte=date) | models.Q(end_date=None)
            )
            if len(geogs) != 1:
                return None
            return geogs[0]


class OrganisationGeography(DateConstraintMixin, models.Model):
    organisation = models.ForeignKey(Organisation, related_name='geographies')
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    gss = models.CharField(blank=True, max_length=20)
    legislation_url = models.CharField(blank=True, max_length=500, null=True)
    geography = models.MultiPolygonField()

    class Meta:
        ordering = ('-start_date',)
        get_latest_by = 'start_date'
        unique_together = (
            ('organisation', 'start_date'),
            ('organisation', 'end_date')
        )
        """
        Note:
        This model also has an additional constraint to prevent
        overlapping start and end dates (but allows both to be NULL).
        This is defined in
        organisations/migrations/0040_end_date_constraint.py
        """


class OrganisationDivisionSet(DateConstraintMixin, models.Model):
    organisation = models.ForeignKey(Organisation, related_name='divisionset')
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=True)
    legislation_url = models.CharField(blank=True, max_length=500, null=True)
    consultation_url = models.CharField(blank=True, max_length=500, null=True)
    short_title = models.CharField(blank=True, max_length=200)
    mapit_generation_id = models.CharField(blank=True, max_length=255)
    notes = models.TextField(blank=True)
    ValidationError = ValueError

    def __str__(self):
        return "{}:{} ({} to {})".format(
            self.pk,
            self.short_title,
            self.start_date,
            self.end_date or "now"
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

    class Meta:
        ordering = ('-start_date',)
        get_latest_by = 'start_date'
        unique_together = ('organisation', 'start_date')
        unique_together = ('organisation', 'end_date')
        """
        Note:
        This model also has an additional constraint to prevent
        overlapping start and end dates which is defined in
        organisations/migrations/0031_end_date_constraint.py
        """


class OrganisationDivision(models.Model):
    """
    Sub parts of an organisation that people can be elected to.

    This could be a ward, constituency or office
    """
    organisation = models.ForeignKey(Organisation, related_name='divisions')
    divisionset = models.ForeignKey(
        OrganisationDivisionSet, related_name='divisions', null=False)
    name = models.CharField(blank=True, max_length=255)
    official_identifier = models.CharField(
        blank=True, max_length=255, db_index=True)
    geography_curie = models.CharField(blank=True, max_length=100)
    slug = models.CharField(blank=True, max_length=100)
    division_type = models.CharField(blank=True, max_length=255)
    division_subtype = models.CharField(blank=True, max_length=255)
    division_election_sub_type = models.CharField(blank=True, max_length=2)
    seats_total = models.IntegerField(blank=True, null=True)
    mapit_generation_low = models.IntegerField(blank=True, null=True)
    mapit_generation_high = models.IntegerField(blank=True, null=True)
    territory_code = models.CharField(blank=True, max_length=10)
    ValidationError = ValueError


    def __str__(self):
        return "{}".format(self.name)

    class Meta:
        ordering = ('name',)
        unique_together = (
            'organisation',
            'divisionset',
            'official_identifier'
        )

    def format_geography_link(self):
        try:
            code_type, code = self.geography_curie.split(':')
        except (ValueError, AttributeError):
            return None

        if code_type.lower() != 'gss':
            return None

        return "https://mapit.mysociety.org/code/{}/{}".format(
            code_type, code
        )

class DivisionGeography(models.Model):
    division = models.OneToOneField(
        OrganisationDivision, related_name="geography")
    geography = models.MultiPolygonField()
