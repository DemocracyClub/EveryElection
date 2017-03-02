from django.core.management.base import BaseCommand

from elections.models import Election
from elections import constants


class Command(BaseCommand):

    def handle(self, *args, **options):
        def _process_qs(qs, geography_type="division"):
            for election in qs:
                geography = getattr(election, geography_type).geography
                election.geography = geography
                election.save()

        # divisions first
        _process_qs(Election.objects.filter(
            group_type=None, geography=None).exclude(division=None))

        # Direct Organisation elections
        _process_qs(Election.objects.filter(
            group_type="organisation",
            geography=None,
            division=None),
            geography_type="organisation")

