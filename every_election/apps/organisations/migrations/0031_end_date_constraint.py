# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("organisations", "0030_auto_20171230_1602")]

    operations = [
        migrations.RunSQL("CREATE EXTENSION IF NOT EXISTS btree_gist;"),
        migrations.RunSQL(
            """
            ALTER TABLE organisations_organisationdivisionset
            ADD CONSTRAINT no_overlaps
            EXCLUDE USING GIST (
                organisation_id WITH =,
                daterange(
                    start_date,
                    CASE WHEN end_date IS NULL
                    THEN 'infinity'::date
                    ELSE end_date END
                ) WITH &&
            );
        """,
            reverse_sql="""
            ALTER TABLE organisations_organisationdivisionset
            DROP CONSTRAINT no_overlaps;
        """,
        ),
    ]
