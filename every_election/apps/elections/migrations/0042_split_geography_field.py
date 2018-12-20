# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def split_geography_field(apps, schema_editor):
    Election = apps.get_model("elections", "Election")
    OrganisationGeography = apps.get_model("organisations", "OrganisationGeography")

    elections = Election.objects.all()
    for election in elections:
        if not election.division_geography:
            continue
        if not election.division_geography.organisation_id:
            continue

        og = OrganisationGeography.objects.all().get(
            organisation_id=election.division_geography.organisation_id
        )
        election.organisation_geography = og
        election.division_geography = None
        election.save()


class Migration(migrations.Migration):

    dependencies = [
        ("organisations", "0040_end_date_constraint"),
        ("elections", "0041_auto_20180607_1141"),
    ]

    operations = [
        migrations.RunPython(split_geography_field, migrations.RunPython.noop)
    ]
