from django.conf import settings
from django.contrib.auth.models import Group, User
from rest_framework.pagination import LimitOffsetPagination


def user_is_moderator(user: User):
    if not user.is_authenticated:
        return False
    group = Group.objects.get(name="moderators")
    return group in user.groups.all()


class MaxSizeLimitOffsetPagination(LimitOffsetPagination):
    max_limit = getattr(settings, "API_MAX_LIMIT", 100)
