# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("organisations", "0033_auto_20180605_0911")]

    operations = [
        migrations.RunSQL("CREATE EXTENSION IF NOT EXISTS btree_gist;"),
        migrations.RunSQL(
            """
            ALTER TABLE organisations_organisation
            ADD CONSTRAINT no_org_overlaps
            EXCLUDE USING GIST (
                official_identifier WITH =,
                organisation_type WITH =,
                daterange(
                    start_date,
                    CASE WHEN end_date IS NULL
                    THEN 'infinity'::date
                    ELSE end_date END
                ) WITH &&
            );
        """,
            reverse_sql="""
            ALTER TABLE organisations_organisation
            DROP CONSTRAINT no_org_overlaps;
        """,
        ),
    ]
