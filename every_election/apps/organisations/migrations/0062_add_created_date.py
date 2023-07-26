# Generated by Django 2.2.20 on 2021-09-28 16:03

from django.db import migrations

from django.db.models import F, OuterRef, Subquery


def add_created_date(apps, schema_editor):
    """
    Set the Organisation created date to the start date value
    Set the OrganisationDivision created date to the start_date of the
    objects related division_set
    """

    Organisation = apps.get_model("organisations", "Organisation")
    Organisation.objects.update(created=F("start_date"))

    OrganisationDivision = apps.get_model(
        "organisations", "OrganisationDivision"
    )
    OrganisationDivisionSet = apps.get_model(
        "organisations", "OrganisationDivisionSet"
    )

    division_set = OrganisationDivisionSet.objects.filter(
        divisions=OuterRef("pk")
    )
    subquery = Subquery(division_set.values("start_date")[:1])
    OrganisationDivision.objects.update(created=subquery)


class Migration(migrations.Migration):
    dependencies = [
        ("organisations", "0061_auto_20210928_1509"),
    ]

    operations = [
        migrations.RunPython(
            code=add_created_date, reverse_code=migrations.RunPython.noop
        )
    ]
