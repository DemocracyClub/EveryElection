# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-10 17:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Organisation",
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
                    "official_identifier",
                    models.CharField(blank=True, db_index=True, max_length=255),
                ),
                ("official_name", models.CharField(blank=True, max_length=255)),
                ("common_name", models.CharField(blank=True, max_length=255)),
                ("gss", models.CharField(blank=True, max_length=20)),
                ("slug", models.CharField(blank=True, max_length=100)),
                ("country_code", models.CharField(blank=True, max_length=3)),
            ],
        )
    ]
