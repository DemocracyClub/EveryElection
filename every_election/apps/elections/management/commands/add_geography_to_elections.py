from django.core.management.base import BaseCommand
from django.db import models

from elections.models import Election


class Command(BaseCommand):

    def handle(self, *args, **options):

        # divisions first
        elections = Election.objects.filter(
                group_type=None,
                division_geography=None
            ).exclude(division=None)
        for election in elections:
            self.stdout.write(str(election))
            election.division_geography = election.get_division_geography()
            election.save()

        # Direct Organisation elections
        elections = Election.objects.filter(
                models.Q(group_type="organisation") | models.Q(group_type=None),
                organisation_geography=None,
                division=None
            ).exclude(organisation=None)
        for election in elections:
            self.stdout.write(str(election))
            election.organisation_geography = election.get_organisation_geography()
            election.save()
