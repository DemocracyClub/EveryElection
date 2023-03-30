# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-07-03 10:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "organisations",
            "0056_divisionproblem_organisationgeographyproblem_organisationproblem",
        )
    ]

    operations = [
        migrations.RemoveField(
            model_name="organisationdivision", name="mapit_generation_high"
        ),
        migrations.RemoveField(
            model_name="organisationdivision", name="mapit_generation_low"
        ),
        migrations.RemoveField(
            model_name="organisationdivisionset", name="mapit_generation_id"
        ),
        migrations.AlterField(
            model_name="organisation",
            name="organisation_type",
            field=models.CharField(
                choices=[
                    ("combined-authority", "combined-authority"),
                    ("sp", "sp"),
                    ("gla", "gla"),
                    ("local-authority", "local-authority"),
                    ("naw", "naw"),
                    ("nia", "nia"),
                    ("parl", "parl"),
                    ("police-area", "police-area"),
                    ("sp", "sp"),
                    ("europarl", "europarl"),
                ],
                default="local-authority",
                max_length=255,
            ),
        ),
    ]
