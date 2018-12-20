# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def copy_status_data(apps, schema_editor):
    ModerationHistory = apps.get_model("elections", "ModerationHistory")
    Election = apps.get_model("elections", "Election")
    ModerationStatus = apps.get_model("elections", "ModerationStatus")
    for election in Election.private_objects.all():
        rec = ModerationHistory(
            election=election,
            status=ModerationStatus.objects.all().get(
                short_label__iexact=election.suggested_status
            ),
        )
        rec.save()


def delete_status_data(apps, schema_editor):
    ModerationHistory = apps.get_model("elections", "ModerationHistory")
    ModerationHistory.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [("elections", "0048_seed_status")]

    operations = [migrations.RunPython(copy_status_data, delete_status_data)]
