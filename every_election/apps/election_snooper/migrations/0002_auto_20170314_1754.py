# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-14 17:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("election_snooper", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="snoopedelection",
            name="date",
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name="snoopedelection",
            name="detail_url",
            field=models.URLField(blank=True, max_length=800),
        ),
    ]
