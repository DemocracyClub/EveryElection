# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-10-05 13:20
from __future__ import unicode_literals

import django.db.models.deletion
import django.db.models.manager
import django_extensions.db.fields
import elections.managers
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("elections", "0046_update_status")]

    operations = [
        migrations.CreateModel(
            name="ModerationHistory",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name="modified"
                    ),
                ),
            ],
            options={
                "ordering": ("-modified", "-created"),
                "get_latest_by": "modified",
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ModerationStatus",
            fields=[
                (
                    "short_label",
                    models.CharField(
                        choices=[
                            (
                                elections.models.ModerationStatuses(
                                    "Suggested"
                                ),
                                "Suggested",
                            ),
                            (
                                elections.models.ModerationStatuses("Rejected"),
                                "Rejected",
                            ),
                            (
                                elections.models.ModerationStatuses("Approved"),
                                "Approved",
                            ),
                            (
                                elections.models.ModerationStatuses("Deleted"),
                                "Deleted",
                            ),
                        ],
                        max_length=32,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("long_label", models.CharField(max_length=100)),
            ],
        ),
        migrations.AlterModelManagers(
            name="election",
            managers=[
                ("public_objects", django.db.models.manager.Manager()),
                (
                    "private_objects",
                    elections.managers.PrivateElectionsManager(),
                ),
            ],
        ),
        migrations.AddField(
            model_name="moderationhistory",
            name="election",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="elections.Election",
            ),
        ),
        migrations.AddField(
            model_name="moderationhistory",
            name="status",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="elections.ModerationStatus",
            ),
        ),
        migrations.AddField(
            model_name="election",
            name="moderation_statuses",
            field=models.ManyToManyField(
                through="elections.ModerationHistory",
                to="elections.ModerationStatus",
            ),
        ),
    ]
