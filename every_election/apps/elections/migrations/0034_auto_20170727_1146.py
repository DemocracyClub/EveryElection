# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-07-27 11:46
from __future__ import unicode_literals

import elections.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("elections", "0033_election_source")]

    operations = [
        migrations.AlterField(
            model_name="document",
            name="uploaded_file",
            field=models.FileField(
                max_length=1000,
                storage=elections.models.PdfS3Storage(),
                upload_to="",
            ),
        )
    ]
