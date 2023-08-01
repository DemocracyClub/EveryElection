# Generated by Django 2.2.20 on 2021-09-28 15:09

import django.utils.timezone
import django_extensions.db.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("organisations", "0060_delete_duplicate_org_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="organisation",
            name="created",
            field=django_extensions.db.fields.CreationDateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name="created",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="organisation",
            name="modified",
            field=django_extensions.db.fields.ModificationDateTimeField(
                auto_now=True, verbose_name="modified"
            ),
        ),
        migrations.AddField(
            model_name="organisationdivision",
            name="created",
            field=django_extensions.db.fields.CreationDateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name="created",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="organisationdivision",
            name="modified",
            field=django_extensions.db.fields.ModificationDateTimeField(
                auto_now=True, verbose_name="modified"
            ),
        ),
    ]
