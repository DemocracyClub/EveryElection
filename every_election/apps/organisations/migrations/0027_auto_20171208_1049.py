# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-12-08 10:49
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("organisations", "0026_auto_20171207_1417")]

    operations = [
        migrations.AlterField(
            model_name="organisationdivision",
            name="divisionset",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="divisions",
                to="organisations.OrganisationDivisionSet",
            ),
        )
    ]
