# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-19 12:00
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("organisations", "0043_auto_20180607_1337")]

    operations = [
        migrations.AlterUniqueTogether(
            name="organisation",
            unique_together={
                ("official_identifier", "organisation_type", "start_date"),
                ("official_identifier", "organisation_type", "end_date"),
            },
        ),
        migrations.AlterUniqueTogether(
            name="organisationgeography",
            unique_together={
                ("organisation", "end_date"),
                ("organisation", "start_date"),
            },
        ),
    ]
