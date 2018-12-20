# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("organisations", "0039_auto_20180607_0957")]

    operations = [
        migrations.RunSQL("CREATE EXTENSION IF NOT EXISTS btree_gist;"),
        migrations.RunSQL(
            """
            ALTER TABLE organisations_organisationgeography
            ADD CONSTRAINT no_org_geog_overlaps
            EXCLUDE USING GIST (
                organisation_id WITH =,
                daterange(
                    CASE WHEN start_date IS NULL
                    THEN '-infinity'::date
                    ELSE start_date END,

                    CASE WHEN end_date IS NULL
                    THEN 'infinity'::date
                    ELSE end_date END
                ) WITH &&
            );
            """,
            reverse_sql="""
            ALTER TABLE organisations_organisationgeography
            DROP CONSTRAINT no_org_geog_overlaps;
            """,
        ),
    ]
