# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organisations', '0034_end_date_constraint'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER INDEX no_overlaps RENAME TO no_divset_overlaps;",
            reverse_sql="""
            ALTER INDEX no_divset_overlaps RENAME TO no_overlaps;"""),
    ]
