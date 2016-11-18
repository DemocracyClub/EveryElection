from enum import Enum, unique

from django.db import models


@unique
class SuggestedStatuses(Enum):
    rejected = "Rejected"
    suggested = "Suggested"
    accepted = "Accepted"


class SuggestedByPublicMixin(models.Model):
    suggested_status = models.CharField(
        max_length=255,
        choices=[(x.name, x.value) for x in SuggestedStatuses],
        default=SuggestedStatuses.suggested.value,
    )
    suggestion_reason = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        abstract = True
