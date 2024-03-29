# Generated by Django 2.2.27 on 2022-07-19 21:56

from django.db import migrations
from django.db.models import F, OuterRef, Subquery


def populate_current_status(apps, schema_editor):
    Election = apps.get_model("elections", "Election")
    ModerationHistory = apps.get_model("elections", "ModerationHistory")
    latest_statuses = Subquery(
        ModerationHistory.objects.filter(
            election_id=OuterRef("id"),
        )
        .order_by("-modified")
        .values("status")[:1]
    )

    Election.private_objects.annotate(latest_status=latest_statuses).exclude(
        latest_status=F("current_status")
    ).update(current_status=F("latest_status"))


class Migration(migrations.Migration):
    dependencies = [
        ("elections", "0069_add_current_status"),
    ]

    operations = [
        migrations.RunPython(populate_current_status, migrations.RunPython.noop)
    ]
