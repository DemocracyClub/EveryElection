# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-10-01 11:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("elections", "0043_auto_20180720_1631")]

    operations = [
        migrations.AlterField(
            model_name="election",
            name="suggested_status",
            field=models.CharField(
                choices=[
                    ("suggested", "Suggested"),
                    ("rejected", "Rejected"),
                    ("approved", "Approved"),
                    ("deleted", "Deleted"),
                ],
                default="suggested",
                max_length=255,
            ),
        )
    ]
