# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-10-08 15:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("elections", "0052_auto_20181005_1645")]

    operations = [
        migrations.AlterField(
            model_name="election",
            name="group",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="_children_qs",
                to="elections.Election",
            ),
        )
    ]
