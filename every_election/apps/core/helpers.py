from datetime import date, datetime

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Group, User
from django.http import Http404
from rest_framework.pagination import LimitOffsetPagination


def user_is_moderator(user: User | AnonymousUser):
    if not user.is_authenticated:
        return False
    group = Group.objects.get(name="moderators")
    return group in user.groups.all()


class MaxSizeLimitOffsetPagination(LimitOffsetPagination):
    max_limit = getattr(settings, "API_MAX_LIMIT", 100)


def parse_date_or_404(value: str) -> date:
    """
    Parse a yyyy-mm-dd URL segment. The URL patterns only check that the
    segment is made of digits in the right places, so a value like
    2026-13-45 reaches the view and is treated as not found.

    Raises Http404 rather than a DRF exception so that this can be used
    in Django and DRF views. DRF turns Http404 into NotFound and keeps
    the message.
    """
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise Http404(f"'{value}' is not a valid yyyy-mm-dd date")
