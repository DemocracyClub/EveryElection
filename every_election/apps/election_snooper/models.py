from django.db import models

class SnoopedElection(models.Model):
    source = models.URLField(blank=True)
    snooper_name = models.CharField(blank=True, max_length=100)
    title = models.CharField(blank=True, max_length=800)
    date = models.DateField(null=True)
    cause = models.CharField(blank=True, max_length=800)
    detail_url = models.URLField(blank=True, max_length=800)
    detail = models.TextField(blank=True)
    extra = models.TextField(blank=True)

