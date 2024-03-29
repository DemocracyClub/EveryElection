# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-01-11 14:41
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("organisations", "0011_organisationdivision_seats_total")]

    operations = [
        migrations.CreateModel(
            name="OrganisationDivisionSet",
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
                ("start_date", models.DateField(null=True)),
                ("end_date", models.DateField(null=True)),
                (
                    "organisation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="divisionset",
                        to="organisations.Organisation",
                    ),
                ),
            ],
        ),
        migrations.AlterModelOptions(
            name="organisationdivision", options={"ordering": ("name",)}
        ),
        migrations.RemoveField(
            model_name="organisationdivision", name="end_date"
        ),
        migrations.RemoveField(
            model_name="organisationdivision", name="start_date"
        ),
        migrations.AlterField(
            model_name="organisationdivision",
            name="organisation",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="divisions",
                to="organisations.Organisation",
            ),
        ),
        migrations.AddField(
            model_name="organisationdivision",
            name="divisionset",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="divisions",
                to="organisations.OrganisationDivisionSet",
            ),
        ),
    ]
