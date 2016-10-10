from django.db import models

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

    def __str__(self):
        return "{} ({})".format(
            self.official_name,
            self.official_identifier)

    @property
    def name(self):
        return self.official_name or self.common_name or self.official_identifier
