from django.db import models


class ElectionType(models.Model):
    """
    As defined at https://democracyclub.org.uk/projects/election-ids/reference/
    """

    name = models.CharField(blank=True, max_length=100)
    election_type = models.CharField(blank=True, max_length=100)

class ElectionSubType(models.Model):
    """
    As defined at https://democracyclub.org.uk/projects/election-ids/reference/
    """

    name = models.CharField(blank=True, max_length=100)
    election_type = models.ForeignKey(ElectionType, related_name="subtype")
    election_subtype = models.CharField(blank=True, max_length=100)
