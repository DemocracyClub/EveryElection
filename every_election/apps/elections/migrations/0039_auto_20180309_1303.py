# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-03-09 13:03
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("elections", "0038_auto_20180309_1126")]

    operations = [
        migrations.AlterModelOptions(
            name="metadata", options={"verbose_name_plural": "MetaData"}
        )
    ]
