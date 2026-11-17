import datetime

from django.db import migrations

# Divisionsets whose end_date is the same as their successor's start_date,
# so both are in force on that day.
# All the elections for that day use divsions from the second/later divsionset
# so the old divisionset should end the day before.
#
# (official_identifier, start_date, end_date)
DIVSETS_TO_FIX = [
    # Hastings: 2004 Boundaries, succeeded by
    # The Hastings (Electoral Changes) Order 2016 from 2018-05-03
    ("HAS", datetime.date(2004, 12, 2), datetime.date(2018, 5, 3)),
    # Chelmsford: 2004 Boundaries, succeeded by
    # The Chelmsford (Electoral Changes) Order 2023 from 2023-05-04
    ("CHL", datetime.date(2004, 12, 2), datetime.date(2023, 5, 4)),
]

ONE_DAY = datetime.timedelta(days=1)


def get_divsets(apps, official_identifier, start_date):
    OrganisationDivisionSet = apps.get_model(
        "organisations", "OrganisationDivisionSet"
    )
    return OrganisationDivisionSet.objects.filter(
        organisation__official_identifier=official_identifier,
        organisation__organisation_type="local-authority",
        start_date=start_date,
    )


def fix_end_dates(apps, schema_editor):
    # These rows won't exist in a fresh database (e.g. when running
    # tests), in which case the updates do nothing.
    for official_identifier, start_date, end_date in DIVSETS_TO_FIX:
        get_divsets(apps, official_identifier, start_date).filter(
            end_date=end_date
        ).update(end_date=end_date - ONE_DAY)


def restore_end_dates(apps, schema_editor):
    for official_identifier, start_date, end_date in DIVSETS_TO_FIX:
        get_divsets(apps, official_identifier, start_date).filter(
            end_date=end_date - ONE_DAY
        ).update(end_date=end_date)


class Migration(migrations.Migration):
    dependencies = [
        ("organisations", "0079_divisionset_unique_organisation_start_date"),
    ]

    operations = [
        migrations.RunPython(fix_end_dates, restore_end_dates),
    ]
