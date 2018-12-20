from django.contrib.auth.models import Group


def user_is_moderator(user):
    group = Group.objects.get(name="moderators")
    return group in user.groups.all()
