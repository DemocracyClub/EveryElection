import datetime

from django.db import models
from django.urls import reverse
from model_utils import Choices
from model_utils.models import StatusModel


class SnoopedElection(StatusModel):
    STATUS = Choices(
        ("election", "This is an Election"),
        ("rejected", "Not an election"),
        ("duplicate", "Duplicate"),
        ("out_of_scope", "Election out of scope"),
    )

    source = models.URLField(blank=True)
    snooper_name = models.CharField(blank=True, max_length=100)
    title = models.CharField(blank=True, max_length=800)
    date = models.DateField(null=True)
    cause = models.CharField(blank=True, max_length=800)
    detail_url = models.URLField(blank=True, max_length=800)
    detail = models.TextField(blank=True)
    extra = models.TextField(blank=True)
    date_seen = models.DateField(default=datetime.datetime.today)
    reviewed = models.BooleanField(default=False)
    status = models.CharField(choices=STATUS, default="new", max_length=100)

    def get_absolute_url(self):
        return "{}?pk={}".format(reverse("snooped_election_view"), self.pk)

    def __str__(self):
        return f"{self.title} - {self.date_seen} ({self.snooper_name})"
