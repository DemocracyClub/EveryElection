# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("elections", "0045_auto_20181001_1437")]

    operations = [
        # assume all elections that already exist are approved
        migrations.RunSQL(
            """
            UPDATE elections_election SET suggested_status='approved'
            """,
            reverse_sql="""
            UPDATE elections_election SET suggested_status='suggested'
            """,
        )
    ]
