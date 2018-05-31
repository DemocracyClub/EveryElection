from django.contrib.gis.db import models
from django.urls import reverse


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
    gss = models.CharField(blank=True, max_length=20)
    slug = models.CharField(blank=True, max_length=100)
    territory_code = models.CharField(blank=True, max_length=10)
    election_types = models.ManyToManyField(
        'elections.ElectionType', through='elections.ElectedRole')
    election_name = models.CharField(blank=True, max_length=255)
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=True)
    ValidationError = ValueError

    def __str__(self):
        return "{}".format(self.name)

    @property
    def name(self):
        return self.official_name or self.common_name or self.official_identifier

    class Meta:
        ordering = ('official_name',)

    def get_absolute_url(self):
        return reverse("organisation_view", args=(self.official_identifier,))

    def format_geography_link(self):
        return "https://mapit.mysociety.org/area/{}".format(
            self.gss
        )



class OrganisationDivisionSet(models.Model):
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
        organisations/migrations/0030_end_date_constraint.py
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
        code_type, code = self.geography_curie.split(':')
        return "https://mapit.mysociety.org/code/{}/{}".format(
            code_type, code
        )

class DivisionGeography(models.Model):
    division = models.OneToOneField(
        OrganisationDivision, related_name="geography", null=True)
    organisation = models.OneToOneField(
        Organisation, related_name="geography", null=True)
    geography = models.MultiPolygonField()

