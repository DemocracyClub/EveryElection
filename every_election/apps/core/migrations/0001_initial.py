# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.contrib.auth.models import Group, User


def add_moderator_group(apps, schema_editor):
    g = Group.objects.create(name="moderators")
    g.save()
    for user in User.objects.all():
        # add any existing admin users
        # to the moderators group when we create it
        if user.is_superuser:
            g.user_set.add(user)


class Migration(migrations.Migration):

    dependencies = [("auth", "0008_alter_user_username_max_length")]

    operations = [migrations.RunPython(add_moderator_group)]
