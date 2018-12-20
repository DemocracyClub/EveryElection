# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def load_init_data(apps, schema_editor):
    ModerationStatus = apps.get_model("elections", "ModerationStatus")
    recs = [
        ModerationStatus(
            short_label="Suggested", long_label="Suggested by an anonymous user"
        ),
        ModerationStatus(short_label="Rejected", long_label="Rejected by a moderator"),
        ModerationStatus(short_label="Approved", long_label="Approved by a moderator"),
        ModerationStatus(
            short_label="Deleted", long_label="Deleted (because it was added in error)"
        ),
    ]
    ModerationStatus.objects.bulk_create(recs)


def delete_init_data(apps, schema_editor):
    ModerationStatus = apps.get_model("elections", "ModerationStatus")
    ModerationStatus.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [("elections", "0047_auto_20181005_1320")]

    operations = [migrations.RunPython(load_init_data, delete_init_data)]
