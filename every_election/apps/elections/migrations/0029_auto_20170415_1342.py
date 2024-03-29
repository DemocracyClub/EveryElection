# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-04-15 13:42
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("elections", "0028_auto_20170415_1319")]

    operations = [
        migrations.AlterField(
            model_name="election",
            name="explanation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="elections.Explanation",
            ),
        ),
        migrations.AlterField(
            model_name="election",
            name="geography",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="organisations.DivisionGeography",
            ),
        ),
    ]
