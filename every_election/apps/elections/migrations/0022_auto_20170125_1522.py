# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-01-25 15:22
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("elections", "0021_votingsystem")]

    operations = [
        migrations.AddField(
            model_name="election",
            name="voting_system",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="elections.VotingSystem",
            ),
        ),
        migrations.AddField(
            model_name="electiontype",
            name="default_voting_system",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="elections.VotingSystem",
            ),
        ),
    ]
