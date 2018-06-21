# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organisations', '0045_organisation_legislation_url'),
    ]

    operations = [
        migrations.RunSQL("""
            UPDATE organisations_organisation
            SET organisation_type='police-area'
            WHERE organisation_type='police_area';
        """,
        reverse_sql="""
            UPDATE organisations_organisation
            SET organisation_type='police_area'
            WHERE organisation_type='police-area';
        """)
    ]
