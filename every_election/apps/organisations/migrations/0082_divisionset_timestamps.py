import django.utils.timezone
import django_extensions.db.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("organisations", "0081_divisionset_inclusive_overlap_constraint"),
    ]

    operations = [
        migrations.AddField(
            model_name="organisationdivisionset",
            name="created",
            field=django_extensions.db.fields.CreationDateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name="created",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="organisationdivisionset",
            name="modified",
            field=django_extensions.db.fields.ModificationDateTimeField(
                auto_now=True, verbose_name="modified"
            ),
        ),
    ]
