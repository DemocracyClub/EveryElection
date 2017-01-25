from django.core.management.base import BaseCommand

from elections.models import VotingSystem
from elections import constants


class Command(BaseCommand):

    def handle(self, *args, **options):

        for system in constants.VOTING_SYSTEMS:
            VotingSystem.objects.update_or_create(
                slug=system['slug'],
                defaults={
                    "name": system['name'],
                    "wikipedia_url": system['wikipedia_url'],
                    "description": system['description'],
                    "uses_party_lists": system['uses_party_lists'],

                }
            )

