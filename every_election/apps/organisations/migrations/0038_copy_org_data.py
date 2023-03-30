# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("organisations", "0037_organisationgeography")]

    operations = [
        migrations.RunSQL(
            """
            INSERT INTO organisations_organisationgeography (
                organisation_id, geography, gss
            ) (
                SELECT organisation_id, geography, ''
                FROM organisations_divisiongeography WHERE organisation_id IS NOT NULL
            );""",
            reverse_sql="DELETE FROM organisations_organisationgeography;",
        ),
        migrations.RunSQL(
            """
            UPDATE organisations_organisationgeography AS og
            SET gss=o.gss
            FROM organisations_organisation o
            WHERE og.organisation_id=o.id;""",
            reverse_sql="DELETE FROM organisations_organisationgeography;",
        ),
    ]
