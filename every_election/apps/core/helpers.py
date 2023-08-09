from django.contrib.auth.models import Group, User


def user_is_moderator(user: User):
    if not user.is_authenticated:
        return False
    group = Group.objects.get(name="moderators")
    return group in user.groups.all()
