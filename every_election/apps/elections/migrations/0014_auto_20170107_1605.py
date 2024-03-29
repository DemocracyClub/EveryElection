# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-01-07 16:05
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("elections", "0013_election_group")]

    operations = [
        migrations.AlterField(
            model_name="election",
            name="division",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="organisations.OrganisationDivision",
            ),
        ),
        migrations.AlterField(
            model_name="election",
            name="seats_contested",
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name="election",
            name="seats_total",
            field=models.IntegerField(null=True),
        ),
    ]
