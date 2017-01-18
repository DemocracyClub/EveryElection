from django.db import models
from django.core.urlresolvers import reverse


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

    def __str__(self):
        return "{}".format(self.name)

    @property
    def name(self):
        return self.official_name or self.common_name or self.official_identifier

    class Meta:
        ordering = ('official_name',)

    def get_absolute_url(self):
        return reverse("organisation_view", args=(self.official_identifier,))


class OrganisationDivisionSet(models.Model):
    organisation = models.ForeignKey(Organisation, related_name='divisionset')
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    legislation_url = models.CharField(blank=True, max_length=500, null=True)
    consultation_url = models.CharField(blank=True, max_length=500, null=True)
    short_title = models.CharField(blank=True, max_length=200)
    mapit_generation_id = models.CharField(blank=True, max_length=255)
    notes = models.TextField(blank=True)

    def __str__(self):
        return "{}".format(self.short_title)

    class Meta:
        ordering = ('-start_date',)

class OrganisationDivision(models.Model):
    """
    Sub parts of an organisation that people can be elected to.

    This could be a ward, constituency or office
    """
    organisation = models.ForeignKey(Organisation, related_name='divisions')
    divisionset = models.ForeignKey(
        OrganisationDivisionSet, related_name='divisions', null=True)
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


    def __str__(self):
        return "{}".format(self.name)

    class Meta:
        ordering = ('name',)

    def format_geography_link(self):
        code_type, code = self.geography_curie.split(':')
        return "https://mapit.mysociety.org/code/{}/{}".format(
            code_type, code
        )
