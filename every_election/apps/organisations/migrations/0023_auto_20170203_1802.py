# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-02-03 18:02
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("organisations", "0022_divisiongeography")]

    operations = [
        migrations.AlterField(
            model_name="divisiongeography",
            name="division",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="geography",
                to="organisations.OrganisationDivision",
            ),
        ),
        migrations.AlterField(
            model_name="divisiongeography",
            name="organisation",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="geography",
                to="organisations.Organisation",
            ),
        ),
    ]
