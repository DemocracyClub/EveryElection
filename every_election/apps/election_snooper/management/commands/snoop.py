from django.core.management.base import BaseCommand

from election_snooper.snoopers.aldc import ALDCScraper
from election_snooper.snoopers.customsearch import CustomSearchScraper


class Command(BaseCommand):

    # def add_arguments(self, parser):
    #     parser.add_argument('sample', nargs='+')

    def handle(self, *args, **options):
        ALDCScraper().get_all()
        CustomSearchScraper().get_all()
