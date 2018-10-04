from collections import namedtuple
from enum import Enum, unique
from django.db import models


Status = namedtuple('Status', ['short_title', 'long_title'])

@unique
class SuggestedStatuses(Enum):
    suggested = Status("Suggested", "Suggested by an anonymous user")
    rejected = Status("Rejected", "Rejected by a moderator")
    approved = Status("Approved", "Approved by a moderator")
    deleted = Status("Deleted", "Deleted (because it was added in error)")

class SuggestedByPublicMixin(models.Model):
    suggested_status = models.CharField(
        max_length=255,
        choices=[(x.name, x.value.short_title) for x in SuggestedStatuses],
        default=SuggestedStatuses.suggested.value.short_title.lower(),
    )
    suggestion_reason = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        abstract = True
