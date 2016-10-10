# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-10 18:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organisations', '0003_organisation_organisation_subtype'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organisation',
            name='country_code',
        ),
        migrations.AddField(
            model_name='organisation',
            name='territory_code',
            field=models.CharField(blank=True, max_length=10),
        ),
    ]
