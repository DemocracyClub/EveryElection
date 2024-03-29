# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-01-09 15:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("elections", "0015_rename_mayor_type")]

    operations = [
        migrations.AlterField(
            model_name="election",
            name="suggested_status",
            field=models.CharField(
                choices=[
                    ("rejected", "Rejected"),
                    ("suggested", "Suggested"),
                    ("accepted", "Accepted"),
                ],
                default="suggested",
                max_length=255,
            ),
        )
    ]
