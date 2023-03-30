# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-06-28 07:49
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import model_utils.fields


class Migration(migrations.Migration):
    dependencies = [
        ("elections", "0030_merge_20170424_1402"),
        ("election_snooper", "0004_auto_20170627_1405"),
    ]

    operations = [
        migrations.AddField(
            model_name="snoopedelection",
            name="election",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="elections.Election",
            ),
        ),
        migrations.AlterField(
            model_name="snoopedelection",
            name="status",
            field=model_utils.fields.StatusField(
                choices=[(0, "dummy")],
                default="duplicate",
                max_length=100,
                no_check_for_status=True,
                verbose_name="status",
            ),
        ),
    ]
