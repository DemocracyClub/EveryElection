# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("organisations", "0041_auto_20180607_1322")]

    operations = [
        migrations.RunSQL(
            """
            DELETE
            FROM organisations_divisiongeography
            WHERE division_id IS NULL;"""
        )
    ]
