# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("organisations", "0053_auto_20180705_1041")]

    operations = [
        migrations.RunSQL(
            """
            UPDATE organisations_organisationgeography
            SET source='unknown';
            """
        ),
        migrations.RunSQL(
            """
            UPDATE organisations_divisiongeography
            SET source='unknown';
            """
        ),
        migrations.RunSQL(
            """
            UPDATE public.organisations_divisiongeography AS dg
            SET source='lgbce'
            FROM organisations_organisationdivision od
            WHERE od.id=dg.division_id
            AND LEFT(od.official_identifier,4) != 'gss:'
            AND LEFT(od.official_identifier,8) != 'unit_id:'
            AND LEFT(od.official_identifier,9) != 'osni_oid:';
            """
        ),
    ]
