# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("organisations", "0048_auto_20180627_1420")]

    operations = [
        migrations.RunSQL(
            """
        UPDATE organisations_organisationdivision
        SET official_identifier = geography_curie
        WHERE official_identifier != geography_curie;
        """
        )
    ]
