# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-06-23 13:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("organisations", "0024_auto_20170210_1537")]

    operations = [
        migrations.AddField(
            model_name="organisationdivision",
            name="territory_code",
            field=models.CharField(blank=True, max_length=10),
        )
    ]
